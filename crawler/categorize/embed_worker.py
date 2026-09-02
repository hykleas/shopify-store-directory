"""category IS NULL olan urunleri embed eder.

Metin = title + " " + product_type + " " + tags
Model CPU'da calisir; 256'lik batch'lerde ~50.000 urun/4 saat hedefi tutar.

Tek basina:  python -m categorize.embed_worker
"""
from __future__ import annotations

import asyncio
import contextlib
import time

from categorize import vectors
from categorize.text import build_text
from core import config, db
from core.log import get

log = get("categorize.embed")

# embedding'i olmayan urunler. En yeni urunler once (kullanici onlari ariyor).
SELECT_SQL = """
SELECT id, title, product_type, tags, vendor
FROM products
WHERE embedding IS NULL
ORDER BY first_seen_at DESC
LIMIT $1
"""

UPDATE_SQL = """
UPDATE products p
SET embedding = x.vec::vector
FROM (SELECT unnest($1::bigint[]) AS id, unnest($2::text[]) AS vec) x
WHERE p.id = x.id
"""


class EmbedWorker:
    def __init__(self) -> None:
        self.embedded = 0
        self._last_report = time.monotonic()

    async def run_once(self) -> int:
        rows = await db.fetch(SELECT_SQL, config.EMBED_BATCH)
        if not rows:
            return 0

        ids = [r["id"] for r in rows]
        texts = [
            build_text(r["title"], r["product_type"], r["tags"], r["vendor"]) for r in rows
        ]

        # Model CPU'yu bloklar; event loop'u tikamamak icin thread'e at.
        matrix = await asyncio.to_thread(vectors.encode, texts, 64)
        literals = [db.vector_literal(matrix[i]) for i in range(len(ids))]

        await db.execute(UPDATE_SQL, ids, literals)
        self.embedded += len(ids)
        return len(ids)

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 120:
            return
        self._last_report = time.monotonic()
        remaining = await db.fetchval(
            "SELECT count(*) FROM products WHERE embedding IS NULL"
        )
        log.info("embed edilen=%d kalan=%s", self.embedded, remaining)

    async def run_forever(self) -> None:
        await vectors.sync_to_db()
        log.info("embed worker basladi (batch=%d)", config.EMBED_BATCH)
        while True:
            try:
                n = await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("embed dongusu hatasi: %s", exc)
                n = 0
                await asyncio.sleep(10)
            await self.report()
            if n == 0:
                await asyncio.sleep(30)


async def main() -> None:
    try:
        await EmbedWorker().run_forever()
    finally:
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
