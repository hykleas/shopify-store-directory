"""Gunluk katalog aktivitesi ozeti.

Hesaplanan tek sey katalogda gozle gorulur degisim:
  new_products     - o gun ilk kez gorulen urun
  removed_products - katalogdan dusen urun
  price_changes    - fiyati degisen varyant sayisi

Satis, ciro, kazanc veya stok adedi HESAPLANMAZ. Ekstra HTTP istegi atilmaz;
tum veri zaten ingest sirasinda alinmis durumda.

Tek basina:  python -m activity.daily_rollup
"""
from __future__ import annotations

import asyncio
import contextlib

from core import db
from core.log import get

log = get("activity.rollup")

# Bugun crawl edilmis magazalar - rollup sadece bunlar icin anlamli.
CRAWLED_TODAY_SQL = """
SELECT id FROM stores
WHERE last_crawled_at >= CURRENT_DATE
ORDER BY id
"""

ROLLUP_SQL = """
WITH crawled AS (
  SELECT unnest($1::bigint[]) AS store_id
),
newp AS (
  SELECT p.store_id, count(*)::int AS n
  FROM products p JOIN crawled c ON c.store_id = p.store_id
  WHERE p.first_seen_at >= CURRENT_DATE
  GROUP BY p.store_id
),
gone AS (
  -- Bugun crawl edildigi halde katalogda gorulmeyen urunler.
  SELECT p.store_id, count(*)::int AS n
  FROM products p JOIN crawled c ON c.store_id = p.store_id
  WHERE p.last_seen_at <  CURRENT_DATE
    AND p.last_seen_at >= CURRENT_DATE - 1
  GROUP BY p.store_id
),
chg AS (
  SELECT p.store_id, count(*)::int AS n
  FROM products p
  JOIN crawled c ON c.store_id = p.store_id
  JOIN variants v ON v.product_id = p.id
  JOIN LATERAL (
    SELECT vh.price_cents
    FROM variant_history vh
    WHERE vh.variant_id = v.id AND vh.observed_on < CURRENT_DATE
    ORDER BY vh.observed_on DESC
    LIMIT 1
  ) prev ON TRUE
  WHERE prev.price_cents IS DISTINCT FROM v.price_cents
  GROUP BY p.store_id
)
INSERT INTO store_metrics (store_id, observed_on, new_products, removed_products, price_changes)
SELECT c.store_id,
       CURRENT_DATE,
       COALESCE(newp.n, 0),
       COALESCE(gone.n, 0),
       COALESCE(chg.n, 0)
FROM crawled c
LEFT JOIN newp ON newp.store_id = c.store_id
LEFT JOIN gone ON gone.store_id = c.store_id
LEFT JOIN chg  ON chg.store_id  = c.store_id
ON CONFLICT (store_id, observed_on) DO UPDATE SET
  new_products     = EXCLUDED.new_products,
  removed_products = EXCLUDED.removed_products,
  price_changes    = EXCLUDED.price_changes
"""

# Fiyat + stokta var/yok anlik goruntusu. Adet yok, olmayacak.
HISTORY_SQL = """
INSERT INTO variant_history (variant_id, observed_on, price_cents, available)
SELECT v.id, CURRENT_DATE, v.price_cents, v.available
FROM variants v
JOIN products p ON p.id = v.product_id
WHERE p.store_id = ANY($1::bigint[])
ON CONFLICT (variant_id, observed_on) DO UPDATE SET
  price_cents = EXCLUDED.price_cents,
  available   = EXCLUDED.available
"""

PRUNE_HISTORY_SQL = """
DELETE FROM variant_history WHERE observed_on < CURRENT_DATE - 400
"""

BATCH = 500


async def run() -> dict[str, int]:
    rows = await db.fetch(CRAWLED_TODAY_SQL)
    store_ids = [r["id"] for r in rows]
    if not store_ids:
        log.info("bugun crawl edilmis magaza yok, rollup atlandi")
        return {"stores": 0}

    done = 0
    for i in range(0, len(store_ids), BATCH):
        chunk = store_ids[i : i + BATCH]
        # Sira onemli: once fiyat farki (dunun kaydina karsi), sonra bugunu yaz.
        await db.execute(ROLLUP_SQL, chunk)
        await db.execute(HISTORY_SQL, chunk)
        done += len(chunk)
        log.debug("rollup %d/%d", done, len(store_ids))

    with contextlib.suppress(Exception):
        await db.execute(PRUNE_HISTORY_SQL)

    log.info("gunluk rollup tamam: %d magaza", done)
    return {"stores": done}


async def main() -> None:
    try:
        await run()
    finally:
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
