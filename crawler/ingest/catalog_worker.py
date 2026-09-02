"""Magaza kataloglarini /products.json uzerinden ceker ve upsert eder.

Tek basina:  python -m ingest.catalog_worker
"""
from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import re
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from core import config, db, http
from core.log import get

log = get("ingest.catalog")

# Priority -> katalogun bayatlama suresi.
DUE_SQL = """
SELECT id, domain, product_count
FROM stores
WHERE is_active
  AND NOT is_hidden
  AND (
    last_crawled_at IS NULL
    OR last_crawled_at < now() - (
      CASE crawl_priority
        WHEN 1 THEN interval '1 day'
        WHEN 2 THEN interval '2 days'
        WHEN 3 THEN interval '3 days'
        WHEN 4 THEN interval '5 days'
        ELSE interval '7 days'
      END
    )
  )
ORDER BY crawl_priority, last_crawled_at NULLS FIRST
LIMIT $1
"""

UPSERT_PRODUCTS_SQL = """
INSERT INTO products (
  store_id, shopify_id, handle, title, vendor, product_type, tags,
  image_url, price_cents, compare_at_cents, published_at, last_seen_at
)
SELECT $1, x.shopify_id, x.handle, x.title, x.vendor, x.product_type, x.tags,
       x.image_url, x.price_cents, x.compare_at_cents, x.published_at, now()
FROM jsonb_to_recordset($2::jsonb) AS x(
  shopify_id       bigint,
  handle           text,
  title            text,
  vendor           text,
  product_type     text,
  tags             text[],
  image_url        text,
  price_cents      int,
  compare_at_cents int,
  published_at     timestamptz
)
ON CONFLICT (store_id, shopify_id) DO UPDATE SET
  handle           = EXCLUDED.handle,
  title            = EXCLUDED.title,
  vendor           = EXCLUDED.vendor,
  product_type     = EXCLUDED.product_type,
  tags             = EXCLUDED.tags,
  image_url        = EXCLUDED.image_url,
  price_cents      = EXCLUDED.price_cents,
  compare_at_cents = EXCLUDED.compare_at_cents,
  published_at     = COALESCE(EXCLUDED.published_at, products.published_at),
  last_seen_at     = now(),
  -- Baslik degistiyse kategori/embedding gecersizdir, yeniden hesaplansin.
  category  = CASE WHEN products.title IS DISTINCT FROM EXCLUDED.title
                   THEN NULL ELSE products.category END,
  niche     = CASE WHEN products.title IS DISTINCT FROM EXCLUDED.title
                   THEN NULL ELSE products.niche END,
  embedding = CASE WHEN products.title IS DISTINCT FROM EXCLUDED.title
                   THEN NULL ELSE products.embedding END,
  image_hash = CASE WHEN products.image_url IS DISTINCT FROM EXCLUDED.image_url
                    THEN NULL ELSE products.image_hash END
RETURNING id, shopify_id
"""

UPSERT_VARIANTS_SQL = """
INSERT INTO variants (product_id, shopify_id, title, price_cents, available)
SELECT x.product_id, x.shopify_id, x.title, x.price_cents, x.available
FROM jsonb_to_recordset($1::jsonb) AS x(
  product_id  bigint,
  shopify_id  bigint,
  title       text,
  price_cents int,
  available   boolean
)
ON CONFLICT (product_id, shopify_id) DO UPDATE SET
  title       = EXCLUDED.title,
  price_cents = EXCLUDED.price_cents,
  available   = EXCLUDED.available
"""

# Denormalize alanlari tek sorguda tazele.
REFRESH_STORE_SQL = """
UPDATE stores s SET
  product_count   = agg.cnt,
  min_price_cents = agg.min_p,
  max_price_cents = agg.max_p,
  avg_price_cents = agg.avg_p,
  launch_date     = agg.launch,
  last_crawled_at = now(),
  fail_count      = 0,
  crawl_priority  = CASE
      WHEN s.first_seen_at > now() - interval '30 days' THEN 1
      WHEN agg.cnt > s.product_count THEN 1
      WHEN agg.cnt = 0 THEN 5
      ELSE 3
    END
FROM (
  SELECT count(*)                          AS cnt,
         min(price_cents)                  AS min_p,
         max(price_cents)                  AS max_p,
         avg(price_cents)::int             AS avg_p,
         min(published_at)::date           AS launch
  FROM products
  WHERE store_id = $1 AND last_seen_at > now() - interval '2 days'
) agg
WHERE s.id = $1
"""

MARK_FAIL_SQL = """
UPDATE stores
SET fail_count = fail_count + 1,
    last_crawled_at = now(),
    is_active = (fail_count + 1) < 3
WHERE id = $1
RETURNING fail_count, is_active
"""

_SITEMAP_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
_SITEMAP_IMG = re.compile(r"<image:loc>\s*([^<\s]+)\s*</image:loc>", re.I)
_SITEMAP_TITLE = re.compile(r"<image:title>\s*(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?\s*</image:title>", re.I | re.S)


def stable_id(text: str) -> int:
    """Surecler arasi degismeyen, bigint'e sigan pozitif id."""
    digest = hashlib.md5(text.encode("utf-8")).digest()  # noqa: S324 - kriptografik amac yok
    return int.from_bytes(digest[:6], "big")  # < 2^48


def to_cents(value: Any) -> int | None:
    """'19.99' -> 1999. Para hicbir yerde float tutulmaz."""
    if value is None or value == "":
        return None
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if d < 0 or d > Decimal("100000000"):
        return None
    return int((d * 100).quantize(Decimal("1")))


def parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _txt(value: Any, limit: int) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip()
    return v[:limit] or None


def normalize_product(raw: dict) -> tuple[dict, list[dict]] | None:
    """products.json ogesini DB satirlarina cevirir."""
    pid = raw.get("id")
    if not isinstance(pid, int):
        return None
    title = _txt(raw.get("title"), 500)
    handle = _txt(raw.get("handle"), 255)
    if not title or not handle:
        return None

    variants_raw = raw.get("variants") or []
    variants: list[dict] = []
    prices: list[int] = []
    compares: list[int] = []
    for v in variants_raw:
        if not isinstance(v, dict) or not isinstance(v.get("id"), int):
            continue
        cents = to_cents(v.get("price"))
        if cents is not None:
            prices.append(cents)
        cmp_cents = to_cents(v.get("compare_at_price"))
        if cmp_cents is not None:
            compares.append(cmp_cents)
        variants.append(
            {
                "shopify_id": v["id"],
                "title": _txt(v.get("title"), 255),
                "price_cents": cents,
                # Sadece stokta var/yok. Adet HICBIR ZAMAN sorgulanmaz.
                "available": bool(v.get("available")) if v.get("available") is not None else None,
            }
        )

    images = raw.get("images") or []
    image_url = None
    if images and isinstance(images[0], dict):
        image_url = _txt(images[0].get("src"), 1000)
    elif isinstance(raw.get("image"), dict):
        image_url = _txt(raw["image"].get("src"), 1000)

    tags = raw.get("tags")
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    if not isinstance(tags, list):
        tags = []
    tags = [str(t)[:80] for t in tags[:40]]

    published = parse_ts(raw.get("published_at")) or parse_ts(raw.get("created_at"))

    product = {
        "shopify_id": pid,
        "handle": handle,
        "title": title,
        "vendor": _txt(raw.get("vendor"), 255),
        "product_type": _txt(raw.get("product_type"), 255),
        "tags": tags,
        "image_url": image_url,
        "price_cents": min(prices) if prices else None,
        "compare_at_cents": min(compares) if compares else None,
        "published_at": published.isoformat() if published else None,
    }
    return product, variants


async def fetch_catalog(domain: str) -> tuple[list[dict], bool]:
    """Tum sayfalari gezerek ham urun listesini dondurur. (urunler, erisildi_mi)"""
    out: list[dict] = []
    reached = False
    for page in range(1, config.INGEST_MAX_PAGES + 1):
        url = "https://" + domain + "/products.json?limit=250&page=" + str(page)
        r = await http.fetch(url, check_robots=True, retries=2, timeout=15)
        if r is None:
            break
        if r.status in (401, 402, 403, 404, 410):
            break
        if not r.ok:
            break
        data = r.json()
        if not isinstance(data, dict):
            break
        reached = True
        items = data.get("products")
        if not isinstance(items, list) or not items:
            break
        out.extend(i for i in items if isinstance(i, dict))
        if len(items) < 250:
            break
    return out, reached


async def fetch_sitemap_fallback(domain: str) -> list[dict]:
    """products.json kapaliysa urun sitemap'inden baslik + gorsel toplar.

    Fiyat/varyant yok - bilincli olarak degraded. Ekstra istek atmiyoruz.
    """
    url = "https://" + domain + "/sitemap_products_1.xml"
    r = await http.fetch(url, check_robots=True, retries=1, timeout=15)
    if r is None or not r.ok or "<urlset" not in r.text:
        return []

    locs = _SITEMAP_LOC.findall(r.text)
    imgs = _SITEMAP_IMG.findall(r.text)
    titles = [t.strip() for t in _SITEMAP_TITLE.findall(r.text)]

    products: list[dict] = []
    for idx, loc in enumerate(locs):
        if "/products/" not in loc:
            continue
        handle = loc.rsplit("/products/", 1)[-1].split("?")[0].strip("/")
        if not handle:
            continue
        title = titles[idx] if idx < len(titles) else handle.replace("-", " ")
        products.append(
            {
                # Sitemap'te Shopify id yok; handle'dan kararli bir negatif id turetiyoruz
                # ki ON CONFLICT anahtari calissin ve gercek id gelirse cakismasin.
                # Python'un hash()'i surecler arasi degisir, bu yuzden md5.
                "shopify_id": -stable_id(handle),
                "handle": handle[:255],
                "title": (title or handle)[:500],
                "vendor": None,
                "product_type": None,
                "tags": [],
                "image_url": (imgs[idx][:1000] if idx < len(imgs) else None),
                "price_cents": None,
                "compare_at_cents": None,
                "published_at": None,
            }
        )
    return products


async def store_products(store_id: int, products: list[dict], variants_by_pid: dict[int, list[dict]]) -> int:
    if not products:
        return 0
    written = 0
    # 250'lik dilimler: tek dev jsonb payload'i yerine dengeli round-trip.
    for i in range(0, len(products), 250):
        chunk = products[i : i + 250]
        rows = await db.fetch(UPSERT_PRODUCTS_SQL, store_id, json.dumps(chunk))
        written += len(rows)
        id_map = {r["shopify_id"]: r["id"] for r in rows}
        var_rows: list[dict] = []
        for shopify_id, pid in id_map.items():
            for v in variants_by_pid.get(shopify_id, []):
                var_rows.append({**v, "product_id": pid})
        for j in range(0, len(var_rows), 1000):
            await db.execute(UPSERT_VARIANTS_SQL, json.dumps(var_rows[j : j + 1000]))
    return written


class CatalogWorker:
    def __init__(self) -> None:
        self.stores_done = 0
        self.products_written = 0
        self._last_report = time.monotonic()

    async def ingest_store(self, store_id: int, domain: str) -> None:
        raw, reached = await fetch_catalog(domain)
        if not reached:
            raw = await fetch_sitemap_fallback(domain)
            if raw:
                # Sitemap yolu zaten normalize edilmis satirlar dondurur.
                await store_products(store_id, raw, {})
                await db.execute(REFRESH_STORE_SQL, store_id)
                self.stores_done += 1
                self.products_written += len(raw)
                return
            row = await db.fetchrow(MARK_FAIL_SQL, store_id)
            if row and not row["is_active"]:
                log.info("3 kez ulasilamadi, pasife alindi: %s", domain)
            return

        products: list[dict] = []
        variants_by_pid: dict[int, list[dict]] = {}
        for item in raw:
            norm = normalize_product(item)
            if norm is None:
                continue
            product, variants = norm
            products.append(product)
            if variants:
                variants_by_pid[product["shopify_id"]] = variants

        n = await store_products(store_id, products, variants_by_pid)
        await db.execute(REFRESH_STORE_SQL, store_id)
        self.stores_done += 1
        self.products_written += n
        log.debug("%s: %d urun", domain, n)

    async def _one(self, store_id: int, domain: str, sem: asyncio.Semaphore) -> None:
        async with sem:
            try:
                await self.ingest_store(store_id, domain)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("ingest hatasi %s: %s", domain, exc)
                with contextlib.suppress(Exception):
                    await db.execute(MARK_FAIL_SQL, store_id)

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 60:
            return
        self._last_report = time.monotonic()
        due = await db.fetchval(
            "SELECT count(*) FROM stores WHERE is_active AND NOT is_hidden "
            "AND (last_crawled_at IS NULL OR last_crawled_at < now() - interval '1 day')"
        )
        log.info(
            "magaza_islenen=%d urun_yazilan=%d sirada=%s",
            self.stores_done,
            self.products_written,
            due,
        )

    async def run_once(self) -> int:
        rows = await db.fetch(DUE_SQL, config.INGEST_BATCH)
        if not rows:
            return 0
        sem = asyncio.Semaphore(config.INGEST_CONCURRENCY)
        await asyncio.gather(*(self._one(r["id"], r["domain"], sem) for r in rows))
        return len(rows)

    async def run_forever(self) -> None:
        log.info("katalog worker basladi (batch=%d, eszamanli=%d)",
                 config.INGEST_BATCH, config.INGEST_CONCURRENCY)
        while True:
            try:
                n = await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("katalog dongusu hatasi: %s", exc)
                n = 0
            await self.report()
            if n == 0:
                await asyncio.sleep(30)


async def main() -> None:
    try:
        await CatalogWorker().run_forever()
    finally:
        await http.aclose()
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
