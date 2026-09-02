"""Embedding'i olan urunlere KATEGORI atar.

Nis (220 kirilim) atamasi bilincli olarak yapilmiyor - bkz. DECISIONS #26.
Kisaca: kullandigimiz embedding modeli Ingilizce olmayan urun basliklarini
dogru nise esleyemiyor ve olculen dogruluk kabul edilebilir degildi.
27 kategori kirilimi hem guvenilir hem de filtrelemek icin yeterli.

Kategori kaynagi, oncelik sirasiyla:
  1. Magazanin baglamdan belirlenen kategorisi (stores.context_category) -
     olculen dogruluk 11/14 magaza. Magazalar neredeyse her zaman tek nisli.
  2. O yoksa urunun kendi embedding'ine en yakin taksonomi ornegi.

Benzerlik hesabi tamamen pgvector tarafinda: 384 boyutlu vektorleri agdan
tasimak yerine `<=>` (kosinus mesafesi) ile en yakini DB seciyor.

Tek basina:  python -m categorize.assign_worker
"""
from __future__ import annotations

import asyncio
import contextlib
import time

from categorize import taxonomy, vectors
from core import config, db
from core.log import get

log = get("categorize.assign")

ASSIGN_SQL = """
WITH batch AS (
  SELECT p.id, p.embedding, s.context_category
  FROM products p
  JOIN stores s ON s.id = p.store_id
  WHERE p.category IS NULL AND p.embedding IS NOT NULL
  ORDER BY p.first_seen_at DESC
  LIMIT $1
),
best AS (
  SELECT b.id,
         COALESCE(b.context_category, nv.category) AS category,
         -- Magaza baglami varsa ona guveniyoruz; yoksa urunun kendi skoru.
         CASE WHEN b.context_category IS NOT NULL
              THEN 1.0
              ELSE 1 - (b.embedding <=> nv.embedding)
         END AS score
  FROM batch b
  CROSS JOIN LATERAL (
    SELECT category, embedding
    FROM niche_vectors
    WHERE model = $2
    ORDER BY embedding <=> b.embedding
    LIMIT 1
  ) nv
)
UPDATE products p
SET category = CASE WHEN best.score >= $3 THEN best.category ELSE $4 END,
    niche    = NULL
FROM best
WHERE p.id = best.id
RETURNING p.id, p.category
"""

# Magazanin birincil kategorisi = urunlerinin mod kategorisi.
PRIMARY_CATEGORY_SQL = """
UPDATE stores s
SET primary_category = top.category
FROM (
  SELECT DISTINCT ON (store_id) store_id, category
  FROM products
  WHERE category IS NOT NULL AND category <> $1
  GROUP BY store_id, category
  ORDER BY store_id, count(*) DESC, category
) top
WHERE s.id = top.store_id
  AND s.context_category IS NULL          -- baglam varsa o kazanir
  AND s.primary_category IS DISTINCT FROM top.category
"""


class AssignWorker:
    def __init__(self) -> None:
        self.assigned = 0
        self.uncategorized = 0
        self._last_report = time.monotonic()
        self._last_primary = 0.0

    async def run_once(self) -> int:
        rows = await db.fetch(
            ASSIGN_SQL,
            config.EMBED_BATCH,
            config.EMBED_MODEL,
            config.NICHE_MIN_SCORE,
            taxonomy.UNCATEGORIZED,
        )
        self.assigned += len(rows)
        self.uncategorized += sum(1 for r in rows if r["category"] == taxonomy.UNCATEGORIZED)
        return len(rows)

    async def refresh_primary_categories(self) -> None:
        if time.monotonic() - self._last_primary < 900:
            return
        self._last_primary = time.monotonic()
        with contextlib.suppress(Exception):
            await db.execute(PRIMARY_CATEGORY_SQL, taxonomy.UNCATEGORIZED)

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 120:
            return
        self._last_report = time.monotonic()
        remaining = await db.fetchval(
            "SELECT count(*) FROM products WHERE category IS NULL AND embedding IS NOT NULL"
        )
        ratio = (self.uncategorized / self.assigned * 100) if self.assigned else 0.0
        log.info(
            "atanan=%d uncategorized=%.1f%% kalan=%s", self.assigned, ratio, remaining
        )

    async def run_forever(self) -> None:
        await vectors.sync_to_db()
        log.info("assign worker basladi (esik=%.2f)", config.NICHE_MIN_SCORE)
        while True:
            try:
                n = await self.run_once()
                await self.refresh_primary_categories()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("assign dongusu hatasi: %s", exc)
                n = 0
                await asyncio.sleep(10)
            await self.report()
            if n == 0:
                await asyncio.sleep(30)


async def main() -> None:
    try:
        await AssignWorker().run_forever()
    finally:
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
