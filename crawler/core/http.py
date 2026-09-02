"""Tek merkezi HTTP katmani.

Crawler'daki HER dis istek buradan gecer. Rate limit, retry, blacklist,
robots.txt ve User-Agent tek yerde uygulanir - worker'lar dogrudan httpx
cagirmaz.

Kibarlik sozlesmesi (CLAUDE.md ile ayni):
  * ayni host'a saniyede en fazla 1 istek
  * 429 / 503 -> host 24 saat blacklist
  * bot kimligi User-Agent'ta acik
  * robots.txt'e uyulur
"""
from __future__ import annotations

import asyncio
import contextlib
import json as jsonlib
import time
import urllib.robotparser
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

import httpx

from core import config
from core.log import get

log = get("core.http")

# 429/503 disinda da geri cekilmemiz gereken durum kodlari.
_BACKOFF_STATUSES = {500, 502, 504, 522, 524}
_BLACKLIST_STATUSES = {429, 503}


@dataclass(slots=True)
class Response:
    url: str
    status: int
    headers: dict[str, str]
    text: str = ""
    content: bytes = b""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def json(self) -> Any | None:
        try:
            return jsonlib.loads(self.text)
        except (ValueError, TypeError):
            return None


@dataclass
class _Gate:
    """Host basina kapi: sirali erisim + son istek zamani."""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last: float = 0.0


class Fetcher:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._gates: dict[str, _Gate] = {}
        self._blacklist: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._robots_locks: dict[str, asyncio.Lock] = {}
        self._sem: asyncio.Semaphore | None = None
        self.stats = {"requests": 0, "errors": 0, "blacklisted": 0}

    # --- altyapi ------------------------------------------------------------
    async def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": config.USER_AGENT,
                    "Accept": "application/json, text/html;q=0.9, */*;q=0.5",
                    "Accept-Language": "en",
                },
                follow_redirects=True,
                timeout=httpx.Timeout(config.HTTP_TIMEOUT_S),
                limits=httpx.Limits(
                    max_connections=config.GLOBAL_CONCURRENCY * 2,
                    max_keepalive_connections=config.GLOBAL_CONCURRENCY,
                ),
                verify=True,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _semaphore(self) -> asyncio.Semaphore:
        if self._sem is None:
            self._sem = asyncio.Semaphore(config.GLOBAL_CONCURRENCY)
        return self._sem

    # --- blacklist ----------------------------------------------------------
    def is_blacklisted(self, host: str) -> bool:
        until = self._blacklist.get(host)
        if until is None:
            return False
        if until <= time.time():
            del self._blacklist[host]
            return False
        return True

    def blacklist(self, host: str, ttl: int | None = None) -> None:
        if host not in self._blacklist:
            self.stats["blacklisted"] += 1
            log.warning("host blacklistlendi (%ss): %s", ttl or config.BLACKLIST_TTL_S, host)
        self._blacklist[host] = time.time() + (ttl or config.BLACKLIST_TTL_S)

    # --- rate limit ---------------------------------------------------------
    @staticmethod
    def _interval_for(host: str) -> float:
        if host in config.CDN_HOSTS:
            return config.CDN_MIN_INTERVAL_S
        return config.HOST_MIN_INTERVAL_S

    async def _wait_turn(self, host: str) -> None:
        gate = self._gates.get(host)
        if gate is None:
            gate = self._gates.setdefault(host, _Gate())
        interval = self._interval_for(host)
        async with gate.lock:
            delta = time.monotonic() - gate.last
            if delta < interval:
                await asyncio.sleep(interval - delta)
            gate.last = time.monotonic()

    # --- ana giris ----------------------------------------------------------
    async def fetch(
        self,
        url: str,
        *,
        method: str = "GET",
        timeout: float | None = None,  # noqa: ASYNC109 - httpx'in kendi timeout'una devrediliyor
        retries: int | None = None,
        headers: dict[str, str] | None = None,
        check_robots: bool = False,
        want_bytes: bool = False,
    ) -> Response | None:
        """Istegi yapar. Kalici basarisizlikta / blacklistte None doner."""
        host = urlsplit(url).netloc.lower()
        if not host:
            return None
        if self.is_blacklisted(host):
            return None
        if check_robots and not await self.robots_allows(url):
            log.debug("robots.txt engelledi: %s", url)
            return None

        attempts = config.HTTP_RETRIES if retries is None else retries
        client = await self.client()

        for attempt in range(1, attempts + 1):
            if self.is_blacklisted(host):
                return None
            async with self._semaphore():
                await self._wait_turn(host)
                try:
                    self.stats["requests"] += 1
                    r = await client.request(
                        method,
                        url,
                        headers=headers,
                        timeout=timeout or config.HTTP_TIMEOUT_S,
                    )
                except (httpx.HTTPError, OSError, ValueError) as exc:
                    self.stats["errors"] += 1
                    if attempt == attempts:
                        log.debug("istek basarisiz (%s): %s", type(exc).__name__, url)
                        return None
                    await asyncio.sleep(min(2**attempt, 8))
                    continue

            if r.status_code in _BLACKLIST_STATUSES:
                # Sunucu "yavasla" diyor. 24 saat boyunca bu host'a dokunmuyoruz.
                self.blacklist(host)
                return None

            if r.status_code in _BACKOFF_STATUSES and attempt < attempts:
                await asyncio.sleep(min(2**attempt, 8))
                continue

            is_head = method.upper() == "HEAD"
            raw = b"" if is_head else r.content
            return Response(
                url=str(r.url),
                status=r.status_code,
                headers={k.lower(): v for k, v in r.headers.items()},
                text="" if (is_head or want_bytes) else r.text,
                content=raw,
            )
        return None

    # --- robots -------------------------------------------------------------
    async def robots_allows(self, url: str, path: str | None = None) -> bool:
        parts = urlsplit(url)
        host = parts.netloc.lower()
        target = path if path is not None else (parts.path or "/")
        scheme = parts.scheme or "https"
        parser = await self._robots_for(scheme + "://" + host)
        if parser is None:
            return True  # robots.txt yok / okunamadi -> izin var sayilir
        return parser.can_fetch(config.USER_AGENT, target)

    async def _robots_for(self, origin: str) -> urllib.robotparser.RobotFileParser | None:
        host = urlsplit(origin).netloc.lower()
        if host in self._robots:
            return self._robots[host]
        lock = self._robots_locks.setdefault(host, asyncio.Lock())
        async with lock:
            if host in self._robots:
                return self._robots[host]
            parser: urllib.robotparser.RobotFileParser | None = None
            r = await self.fetch(origin + "/robots.txt", retries=1, check_robots=False)
            if r is not None and r.ok and r.text:
                parser = urllib.robotparser.RobotFileParser()
                with contextlib.suppress(Exception):
                    parser.parse(r.text.splitlines())
            self._robots[host] = parser
            return parser


# Surec genelinde tek ornek.
_fetcher = Fetcher()

fetch = _fetcher.fetch
robots_allows = _fetcher.robots_allows
blacklist = _fetcher.blacklist
is_blacklisted = _fetcher.is_blacklisted
aclose = _fetcher.aclose
stats = _fetcher.stats
