"""certstream akisini dinleyip discovery_queue'yu besler (OPSIYONEL kaynak).

DIKKAT: `wss://certstream.calidog.io` public sunucusu baglantiyi kabul ediyor
ama hicbir mesaj gondermiyor. Bu yuzden varsayilan olarak KAPALI
(ENABLE_CERTSTREAM=false); birincil kesif kaynagi discovery/ct_log_poller.py.
Kendi certstream sunucunu calistiriyorsan CERTSTREAM_URL'i verip bu worker'i
acabilirsin.

Tek basina:  python -m discovery.certstream_listener
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import time

import websockets
from websockets.asyncio.client import connect

from core import config, db
from core.log import get
from discovery.domain_filter import extract

log = get("discovery.certstream")

INSERT_SQL = """
INSERT INTO discovery_queue (domain, source)
SELECT unnest($1::text[]), $2
ON CONFLICT (domain) DO NOTHING
"""


class CertstreamListener:
    def __init__(self, source: str = "certstream") -> None:
        self.source = source
        self.buffer: set[str] = set()
        self.seen = 0
        self.queued = 0
        self._last_flush = time.monotonic()
        self._last_report = time.monotonic()

    async def flush(self, force: bool = False) -> None:
        # 500'luk batch dolunca ya da 30 saniye gecince yaz.
        if not self.buffer:
            return
        if (
            not force
            and len(self.buffer) < config.CERTSTREAM_BATCH
            and time.monotonic() - self._last_flush < 30
        ):
            return
        batch = sorted(self.buffer)
        self.buffer.clear()
        self._last_flush = time.monotonic()
        try:
            await db.execute(INSERT_SQL, batch, self.source)
            self.queued += len(batch)
        except Exception as exc:  # noqa: BLE001
            log.error("kuyruga yazilamadi (%d domain): %s", len(batch), exc)

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 60:
            return
        self._last_report = time.monotonic()
        pending = await db.fetchval(
            "SELECT count(*) FROM discovery_queue WHERE status = 'pending'"
        )
        log.info(
            "sertifika=%d kuyruga_yazilan=%d bekleyen=%s tampon=%d",
            self.seen,
            self.queued,
            pending,
            len(self.buffer),
        )

    def handle(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except ValueError:
            return
        if msg.get("message_type") != "certificate_update":
            return
        self.seen += 1
        leaf = (msg.get("data") or {}).get("leaf_cert") or {}
        domains = leaf.get("all_domains") or []
        self.buffer |= extract(domains)

    async def run(self) -> None:
        backoff = 1.0
        while True:
            try:
                log.info("baglaniliyor: %s", config.CERTSTREAM_URL)
                async with connect(
                    config.CERTSTREAM_URL,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=4 * 1024 * 1024,
                    user_agent_header=config.USER_AGENT,
                ) as ws:
                    log.info("certstream baglandi")
                    backoff = 1.0
                    async for raw in ws:
                        self.handle(raw if isinstance(raw, str) else raw.decode("utf-8", "ignore"))
                        await self.flush()
                        await self.report()
            except asyncio.CancelledError:
                await self.flush(force=True)
                raise
            except (websockets.WebSocketException, OSError, ValueError) as exc:
                log.warning("certstream koptu (%s): %s", type(exc).__name__, exc)
            except Exception as exc:  # noqa: BLE001
                log.error("certstream beklenmedik hata: %s", exc)

            await self.flush(force=True)
            # Ussel backoff, tavan 5 dakika.
            log.info("%.0f sn sonra yeniden denenecek", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 300)


async def main() -> None:
    listener = CertstreamListener()
    try:
        await listener.run()
    finally:
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
