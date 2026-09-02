"""discovery_queue'daki domainlerin Shopify olup olmadigini tespit eder.

Sirali kontrol, ilkinde eslesirse durur:
  1. DNS A kaydi 23.227.38.0/24 icinde mi
  2. HEAD /  -> x-shopid veya x-shopify-stage basligi
  3. GET /meta.json -> 200 ve JSON'da id + myshopify_domain

Tek basina:  python -m discovery.shopify_detector
"""
from __future__ import annotations

import asyncio
import contextlib
import ipaddress
import socket
import time

from core import config, db, http
from core.log import get

log = get("discovery.detector")

# Shopify'in ortak magaza IP blogu.
SHOPIFY_NETS = (ipaddress.ip_network("23.227.38.0/24"),)

CLAIM_SQL = """
UPDATE discovery_queue q
SET status = 'checking'
FROM (
  SELECT id FROM discovery_queue
  WHERE status = 'pending'
  ORDER BY created_at
  LIMIT $1
  FOR UPDATE SKIP LOCKED
) picked
WHERE q.id = picked.id
RETURNING q.id, q.domain, q.attempts
"""

FINISH_SQL = """
UPDATE discovery_queue
SET status = $2, checked_at = now(), attempts = attempts + $3
WHERE id = $1
"""

UPSERT_STORE_SQL = """
INSERT INTO stores (domain, shop_id, name, description, country, currency, language, tld, is_hidden)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
ON CONFLICT (domain) DO UPDATE SET
  shop_id     = COALESCE(EXCLUDED.shop_id, stores.shop_id),
  name        = COALESCE(EXCLUDED.name, stores.name),
  description = COALESCE(EXCLUDED.description, stores.description),
  country     = COALESCE(EXCLUDED.country, stores.country),
  currency    = COALESCE(EXCLUDED.currency, stores.currency),
  language    = COALESCE(EXCLUDED.language, stores.language),
  is_hidden   = stores.is_hidden OR EXCLUDED.is_hidden
RETURNING id
"""


def _tld(domain: str) -> str:
    return domain.rsplit(".", 1)[-1]


def _clean(value: object, limit: int = 500) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip()
    return v[:limit] or None


def _country(value: object) -> str | None:
    v = _clean(value)
    if v and len(v) == 2 and v.isalpha():
        return v.upper()
    return None


def _currency(value: object) -> str | None:
    v = _clean(value)
    if v and len(v) == 3 and v.isalpha():
        return v.upper()
    return None


# DNS sonucu uc durumlu: cozulmedi / cozuldu ama Shopify degil / Shopify blogu.
DNS_UNRESOLVED = "unresolved"
DNS_OTHER = "other"
DNS_SHOPIFY = "shopify"


async def dns_lookup(domain: str) -> str:
    """A kaydina bakar. Domain hic cozulmuyorsa bosuna HTTP istegi atmayiz -
    CT loglarindan gelen domainlerin buyuk kismi henuz yayinda degil."""
    loop = asyncio.get_running_loop()
    try:
        infos = await asyncio.wait_for(
            loop.getaddrinfo(domain, 443, family=socket.AF_INET, type=socket.SOCK_STREAM),
            timeout=5,
        )
    except (TimeoutError, socket.gaierror, OSError, UnicodeError):
        return DNS_UNRESOLVED
    if not infos:
        return DNS_UNRESOLVED
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if any(ip in net for net in SHOPIFY_NETS):
            return DNS_SHOPIFY
    return DNS_OTHER


async def header_is_shopify(domain: str) -> bool:
    r = await http.fetch("https://" + domain + "/", method="HEAD", retries=1, timeout=8)
    if r is None:
        return False
    return "x-shopid" in r.headers or "x-shopify-stage" in r.headers


async def read_meta(domain: str) -> dict | None:
    """meta.json'u okur. Shopify degilse None."""
    r = await http.fetch("https://" + domain + "/meta.json", retries=1, timeout=8)
    if r is None or not r.ok:
        return None
    data = r.json()
    if not isinstance(data, dict):
        return None
    if data.get("id") is None or not data.get("myshopify_domain"):
        return None
    lang = None
    cl = r.headers.get("content-language")
    if cl:
        lang = cl.split(",")[0].strip()[:12] or None
    data["_language"] = lang
    return data


async def save_store(domain: str, meta: dict) -> int | None:
    # robots.txt magaza kokunu yasakliyorsa listelemiyoruz.
    allowed = await http.robots_allows("https://" + domain + "/products.json")
    shop_id = meta.get("id")
    row = await db.fetchrow(
        UPSERT_STORE_SQL,
        domain,
        int(shop_id) if isinstance(shop_id, int | float | str) and str(shop_id).isdigit() else None,
        _clean(meta.get("name"), 200),
        _clean(meta.get("description"), 2000),
        _country(meta.get("country")),
        _currency(meta.get("currency")),
        _clean(meta.get("_language"), 12),
        _tld(domain),
        not allowed,
    )
    if not allowed:
        log.info("robots.txt disallow -> gizlendi: %s", domain)
    return row["id"] if row else None


async def check_domain(domain: str) -> tuple[str, dict | None]:
    """('shopify'|'not_shopify', meta) dondurur."""
    # 1) DNS - ucuz, once bu.
    dns = await dns_lookup(domain)

    # Hic cozulmuyorsa siteye gitmenin anlami yok: hem bos yere ~8sn
    # bekliyorduk hem de gereksiz istek atiyorduk.
    if dns == DNS_UNRESOLVED:
        return "not_shopify", None

    # 2) Header - DNS Shopify blogunu gostermiyorsa da bakariz
    #    (magaza bir CDN'in arkasinda olabilir).
    if dns != DNS_SHOPIFY and not await header_is_shopify(domain):
        return "not_shopify", None

    # 3) meta.json ile dogrula ve verileri al.
    meta = await read_meta(domain)
    if meta is None:
        return "not_shopify", None
    return "shopify", meta


class Detector:
    def __init__(self) -> None:
        self.processed = 0
        self.found = 0
        self._last_report = time.monotonic()

    async def _one(self, row_id: int, domain: str, attempts: int, sem: asyncio.Semaphore) -> None:
        async with sem:
            try:
                status, meta = await asyncio.wait_for(check_domain(domain), timeout=10)
            except (TimeoutError, asyncio.CancelledError):
                await self._retry_or_fail(row_id, attempts, "zaman asimi", domain)
                return
            except Exception as exc:  # noqa: BLE001
                await self._retry_or_fail(row_id, attempts, str(exc)[:120], domain)
                return

            if status == "shopify" and meta is not None:
                try:
                    await save_store(domain, meta)
                    self.found += 1
                except Exception as exc:  # noqa: BLE001
                    log.error("store kaydedilemedi %s: %s", domain, exc)
                    await self._retry_or_fail(row_id, attempts, "db", domain)
                    return

            await db.execute(FINISH_SQL, row_id, status, 1)
            self.processed += 1

    async def _retry_or_fail(self, row_id: int, attempts: int, why: str, domain: str) -> None:
        # 3 deneme sonrasi pes et.
        new_status = "error" if attempts + 1 >= 3 else "pending"
        log.debug("%s -> %s (%s)", domain, new_status, why)
        with contextlib.suppress(Exception):
            await db.execute(FINISH_SQL, row_id, new_status, 1)
        self.processed += 1

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 60:
            return
        self._last_report = time.monotonic()
        pending = await db.fetchval(
            "SELECT count(*) FROM discovery_queue WHERE status = 'pending'"
        )
        total_stores = await db.fetchval("SELECT count(*) FROM stores")
        log.info(
            "kuyruk=%s islenen=%d bulunan=%d toplam_magaza=%s istek=%d blacklist=%d",
            pending,
            self.processed,
            self.found,
            total_stores,
            http.stats["requests"],
            http.stats["blacklisted"],
        )

    async def run_once(self) -> int:
        rows = await db.fetch(CLAIM_SQL, config.DETECTOR_BATCH)
        if not rows:
            return 0
        sem = asyncio.Semaphore(config.DETECTOR_CONCURRENCY)
        await asyncio.gather(
            *(self._one(r["id"], r["domain"], r["attempts"], sem) for r in rows)
        )
        return len(rows)

    async def run_forever(self) -> None:
        log.info("detector basladi (batch=%d, eszamanli=%d)",
                 config.DETECTOR_BATCH, config.DETECTOR_CONCURRENCY)
        while True:
            try:
                n = await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("detector dongusu hatasi: %s", exc)
                n = 0
            await self.report()
            if n == 0:
                await asyncio.sleep(15)


async def main() -> None:
    try:
        await Detector().run_forever()
    finally:
        await http.aclose()
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
