"""Urun yayilimi: ayni gorseli satan magazalari tek canonical altinda toplar.

Iki adim:
  1) hash_missing_images() - gorseli olup image_hash'i olmayan urunlerin
     perceptual hash'ini (phash) hesaplar. Gorsel diske KAYDEDILMEZ, sadece
     hash tutulur (bkz. CLAUDE.md kural 6).
  2) rebuild_matches()     - 8 bantli LSH ile aday uretir, Hamming <= 6 olanlari
     union-find ile gruplar, canonical = gruptaki en kucuk product id.
  3) snapshot_spread()     - canonical basina kac magazada listeleniyor ve
     magazalar arasi fiyat araligi.

Satis/ciro cikarimi yapan hicbir skor uretilmez.

Tek basina:  python -m activity.product_spread
"""
from __future__ import annotations

import asyncio
import contextlib
import io
import time

from core import config, db, http
from core.log import get

log = get("activity.spread")

HASH_BITS = 64
BANDS = 8
BAND_BITS = HASH_BITS // BANDS  # 8 bit
BAND_MASK = (1 << BAND_BITS) - 1
# Cok kalabalik bant kovalari (dumduz beyaz gorseller vb.) patlamayi engellemek icin.
MAX_BUCKET = 400

PENDING_IMAGES_SQL = """
SELECT id, image_url
FROM products
WHERE image_hash IS NULL AND image_url IS NOT NULL
ORDER BY first_seen_at DESC
LIMIT $1
"""

SET_HASH_SQL = """
UPDATE products p
SET image_hash = x.h
FROM (SELECT unnest($1::bigint[]) AS id, unnest($2::text[]) AS h) x
WHERE p.id = x.id
"""

# Hash'i cozulemeyen gorseller tekrar tekrar denenmesin.
MARK_BAD_SQL = """
UPDATE products SET image_url = NULL WHERE id = ANY($1::bigint[])
"""

LOAD_HASHES_SQL = """
SELECT id, store_id, image_hash
FROM products
WHERE image_hash IS NOT NULL AND length(image_hash) = 16
ORDER BY id
"""

WRITE_MATCHES_SQL = """
INSERT INTO product_matches (product_id, canonical_id, distance)
SELECT x.product_id, x.canonical_id, x.distance
FROM (
  SELECT unnest($1::bigint[]) AS product_id,
         unnest($2::bigint[]) AS canonical_id,
         unnest($3::int[])    AS distance
) x
ON CONFLICT (product_id) DO UPDATE SET
  canonical_id = EXCLUDED.canonical_id,
  distance     = EXCLUDED.distance,
  matched_at   = now()
"""

SNAPSHOT_SQL = """
INSERT INTO product_spread (canonical_id, observed_on, store_count, min_price_cents, max_price_cents)
SELECT m.canonical_id,
       CURRENT_DATE,
       count(DISTINCT p.store_id)::int,
       min(p.price_cents),
       max(p.price_cents)
FROM product_matches m
JOIN products p ON p.id = m.product_id
JOIN stores  s ON s.id = p.store_id AND NOT s.is_hidden AND s.is_active
GROUP BY m.canonical_id
HAVING count(DISTINCT p.store_id) > 1
ON CONFLICT (canonical_id, observed_on) DO UPDATE SET
  store_count     = EXCLUDED.store_count,
  min_price_cents = EXCLUDED.min_price_cents,
  max_price_cents = EXCLUDED.max_price_cents
"""

PRUNE_SPREAD_SQL = "DELETE FROM product_spread WHERE observed_on < CURRENT_DATE - 120"


# --- 1) gorsel hash'leme ----------------------------------------------------
def _phash_bytes(raw: bytes) -> str | None:
    """Bayttan 16 hex haneli phash. Cozulemezse None."""
    try:
        import imagehash
        from PIL import Image

        with Image.open(io.BytesIO(raw)) as im:
            im.draft("RGB", (256, 256))  # JPEG'i decode ederken kucult, CPU tasarrufu
            return str(imagehash.phash(im.convert("RGB")))
    except Exception:  # noqa: BLE001 - bozuk/desteklenmeyen gorsel normaldir
        return None


def _thumb_url(url: str) -> str:
    """Shopify CDN'inde kucuk boyut iste: bant genisligi ve CPU tasarrufu."""
    if "cdn.shopify.com" not in url:
        return url
    sep = "&" if "?" in url else "?"
    return url + sep + "width=256"


async def hash_missing_images(limit: int = 2000) -> int:
    rows = await db.fetch(PENDING_IMAGES_SQL, limit)
    if not rows:
        return 0

    ok_ids: list[int] = []
    ok_hashes: list[str] = []
    bad_ids: list[int] = []
    sem = asyncio.Semaphore(8)

    async def one(pid: int, url: str) -> None:
        async with sem:
            r = await http.fetch(_thumb_url(url), retries=1, timeout=15, want_bytes=True)
            if r is None or not r.ok or not r.content or len(r.content) > 8_000_000:
                bad_ids.append(pid)
                return
            h = await asyncio.to_thread(_phash_bytes, r.content)
            if h and len(h) == 16:
                ok_ids.append(pid)
                ok_hashes.append(h)
            else:
                bad_ids.append(pid)

    await asyncio.gather(*(one(r["id"], r["image_url"]) for r in rows))

    if ok_ids:
        await db.execute(SET_HASH_SQL, ok_ids, ok_hashes)
    if bad_ids:
        await db.execute(MARK_BAD_SQL, bad_ids)
    log.info("gorsel hash: %d basarili, %d atlandi", len(ok_ids), len(bad_ids))
    return len(ok_ids)


# --- 2) eslestirme ----------------------------------------------------------
class _Union:
    """Yol sikistirmali union-find."""

    def __init__(self) -> None:
        self.parent: dict[int, int] = {}

    def find(self, x: int) -> int:
        p = self.parent.setdefault(x, x)
        while p != x:
            x, p = p, self.parent.setdefault(p, p)
            self.parent[x] = p
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # Kucuk id her zaman kok olsun: canonical kararli kalir.
            if ra < rb:
                self.parent[rb] = ra
            else:
                self.parent[ra] = rb


def _bands(value: int) -> list[int]:
    return [(value >> (i * BAND_BITS)) & BAND_MASK for i in range(BANDS)]


def group_by_hash(
    items: list[tuple[int, int, int]], max_distance: int
) -> dict[int, tuple[int, int]]:
    """[(product_id, store_id, hash_int)] -> {product_id: (canonical_id, distance)}

    Hamming <= 6 olan iki hash, 8 bantin en az ikisinde birebir aynidir
    (guvercin yuvasi), bu yuzden bant esitligi ile aday uretmek kayipsiz.
    """
    buckets: dict[tuple[int, int], list[int]] = {}
    hash_of: dict[int, int] = {}
    store_of: dict[int, int] = {}

    for pid, store_id, value in items:
        hash_of[pid] = value
        store_of[pid] = store_id
        for band_idx, band_val in enumerate(_bands(value)):
            buckets.setdefault((band_idx, band_val), []).append(pid)

    uf = _Union()
    compared = 0
    for members in buckets.values():
        if len(members) < 2 or len(members) > MAX_BUCKET:
            continue
        for i in range(len(members)):
            a = members[i]
            ha = hash_of[a]
            for j in range(i + 1, len(members)):
                b = members[j]
                compared += 1
                if (ha ^ hash_of[b]).bit_count() <= max_distance:
                    uf.union(a, b)

    groups: dict[int, list[int]] = {}
    for pid in hash_of:
        groups.setdefault(uf.find(pid), []).append(pid)

    out: dict[int, tuple[int, int]] = {}
    for canonical, members in groups.items():
        if len(members) < 2:
            continue
        # Tek magazanin kendi icindeki varyantlari "yayilim" degildir.
        if len({store_of[m] for m in members}) < 2:
            continue
        base = hash_of[canonical]
        for pid in members:
            out[pid] = (canonical, (base ^ hash_of[pid]).bit_count())
    log.debug("karsilastirma=%d grup=%d", compared, len(out))
    return out


async def rebuild_matches() -> int:
    rows = await db.fetch(LOAD_HASHES_SQL)
    items: list[tuple[int, int, int]] = []
    for r in rows:
        try:
            items.append((r["id"], r["store_id"], int(r["image_hash"], 16)))
        except (ValueError, TypeError):
            continue
    if not items:
        log.info("hash'lenmis urun yok, eslestirme atlandi")
        return 0

    started = time.monotonic()
    mapping = await asyncio.to_thread(group_by_hash, items, config.PHASH_MAX_DISTANCE)
    log.info(
        "%d hash tarandi, %d urun eslesti (%.1f sn)",
        len(items),
        len(mapping),
        time.monotonic() - started,
    )
    if not mapping:
        return 0

    pids = list(mapping.keys())
    for i in range(0, len(pids), 5000):
        chunk = pids[i : i + 5000]
        await db.execute(
            WRITE_MATCHES_SQL,
            chunk,
            [mapping[p][0] for p in chunk],
            [mapping[p][1] for p in chunk],
        )
    return len(mapping)


# --- 3) gunluk yayilim anlik goruntusu --------------------------------------
async def snapshot_spread() -> None:
    await db.execute(SNAPSHOT_SQL)
    with contextlib.suppress(Exception):
        await db.execute(PRUNE_SPREAD_SQL)
    log.info("yayilim anlik goruntusu yazildi")


async def run(hash_limit: int = 4000) -> dict[str, int]:
    hashed = await hash_missing_images(hash_limit)
    matched = await rebuild_matches()
    await snapshot_spread()
    return {"hashed": hashed, "matched": matched}


async def main() -> None:
    try:
        await run()
    finally:
        await http.aclose()
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
