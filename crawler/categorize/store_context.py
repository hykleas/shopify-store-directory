"""Magaza duzeyinde kategori onseli.

Neden: tek bir urun basligindan 220 nis arasindan dogru olani secmek zayif
sinyal - olculen dogruluk %46. Shopify magazalari neredeyse her zaman tek
nisli; magazanin adi + aciklamasi + en sik product_type'lari + ornek
basliklari birlikte cok daha guclu sinyal veriyor (olculen: urun agirlikli
%84 kategori dogrulugu).

Akis: magaza baglamini olusturan her parca ayri ayri embed edilir, her parca
en yakin nis ornegine oy verir, oylar kategori duzeyinde skorla agirliklandirilip
toplanir. Kazanan kategori `stores.context_category` olarak yazilir ve
assign_worker urun nisini SADECE o kategori icinde arar.

Tek basina:  python -m categorize.store_context
"""
from __future__ import annotations

import asyncio
import contextlib
import time
from collections import defaultdict

from categorize import vectors
from core import config, db
from core.log import get

log = get("categorize.store_ctx")

# Baglami eskimis ya da hic hesaplanmamis magazalar.
DUE_SQL = """
SELECT id, domain, name, description
FROM stores
WHERE product_count > 0
  AND NOT is_hidden
  AND (context_at IS NULL OR context_at < now() - interval '14 days')
ORDER BY context_at NULLS FIRST, product_count DESC
LIMIT $1
"""

TYPES_SQL = """
SELECT product_type, count(*) AS c
FROM products
WHERE store_id = $1 AND product_type IS NOT NULL AND product_type <> ''
GROUP BY product_type ORDER BY c DESC LIMIT 12
"""

TITLES_SQL = """
SELECT title FROM products WHERE store_id = $1 ORDER BY md5(id::text) LIMIT 12
"""

SAVE_SQL = """
UPDATE stores
SET context_category = $2,
    context_score    = $3,
    context_at       = now(),
    -- Magaza kategorisi artik dogrudan baglamdan geliyor; urun modundan
    -- turetmek hem gec kaliyor hem de daha kotu (bkz. DECISIONS #27).
    primary_category = COALESCE($2, primary_category)
WHERE id = $1
"""

# Magaza adinin/aciklamasinin agirligi: product_type'lardan daha az guvenilir
# (cogu magaza adi marka ismi, urun hakkinda bilgi tasimiyor).
WEIGHTS = {"name": 0.7, "description": 0.8, "type": 1.4, "title": 1.0}

# Hicbir sey soylemeyen jenerik product_type'lar.
GENERIC_TYPES = {
    "simple", "downloadable", "virtual", "simple, downloadable, virtual",
    "default", "product", "products", "all products", "all", "untitled",
    "misc", "other", "genel", "diger", "variable",
}


def build_context(
    name: str | None,
    description: str | None,
    product_types: list[tuple[str, int]],
    titles: list[str],
) -> list[tuple[str, float]]:
    """(metin, agirlik) parcalari. Bos ve jenerik olanlar elenir."""
    parts: list[tuple[str, float]] = []
    if name and name.strip():
        parts.append((name.strip()[:120], WEIGHTS["name"]))
    if description and description.strip():
        parts.append((description.strip()[:300], WEIGHTS["description"]))
    for ptype, count in product_types:
        if ptype.strip().casefold() in GENERIC_TYPES:
            continue
        # Cok kullanilan product_type daha guclu oy kullansin (log ile yumusatilmis).
        weight = WEIGHTS["type"] * (1.0 + min(count, 200) / 200)
        parts.append((ptype.strip()[:120], weight))
    for title in titles:
        if title and title.strip():
            parts.append((title.strip()[:120], WEIGHTS["title"]))
    return parts


def predict_category(
    parts: list[tuple[str, float]],
    categories: list[str],
    matrix,
) -> tuple[str | None, float]:
    """Kategori oylamasi -> (kategori, guven 0..1)."""
    if not parts:
        return None, 0.0
    embeddings = vectors.encode([text for text, _ in parts], 64)
    sim = embeddings @ matrix.T

    votes: dict[str, float] = defaultdict(float)
    for i, (_, weight) in enumerate(parts):
        j = int(sim[i].argmax())
        votes[categories[j]] += float(sim[i][j]) * weight

    if not votes:
        return None, 0.0
    ranked = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)
    best, best_score = ranked[0]
    total = sum(votes.values()) or 1.0
    # Guven = kazananin toplam oy icindeki payi.
    return best, best_score / total


class StoreContextWorker:
    def __init__(self) -> None:
        self.done = 0
        self._last_report = time.monotonic()
        self._categories: list[str] | None = None
        self._matrix = None

    def _niche_space(self):
        if self._matrix is None:
            examples, matrix = vectors.build_niche_vectors()
            self._categories = [category for category, _, _, _ in examples]
            self._matrix = matrix
        return self._categories, self._matrix

    async def process(self, store: dict) -> None:
        types = await db.fetch(TYPES_SQL, store["id"])
        titles = await db.fetch(TITLES_SQL, store["id"])
        parts = build_context(
            store["name"],
            store["description"],
            [(t["product_type"], t["c"]) for t in types],
            [t["title"] for t in titles],
        )
        categories, matrix = self._niche_space()
        category, score = await asyncio.to_thread(
            predict_category, parts, categories, matrix
        )
        # Guven cok dusukse kategori dayatmayiz; urun bazli atama serbest kalir.
        if category is None or score < config.STORE_CONTEXT_MIN_SCORE:
            category, score = None, score
        await db.execute(SAVE_SQL, store["id"], category, round(score, 4))
        self.done += 1
        log.debug("%s -> %s (%.2f)", store["domain"], category, score)

    async def report(self) -> None:
        if time.monotonic() - self._last_report < 120:
            return
        self._last_report = time.monotonic()
        remaining = await db.fetchval(
            "SELECT count(*) FROM stores WHERE product_count > 0 AND context_at IS NULL"
        )
        log.info("magaza baglami: islenen=%d kalan=%s", self.done, remaining)

    async def run_once(self) -> int:
        rows = await db.fetch(DUE_SQL, 50)
        for row in rows:
            try:
                await self.process(dict(row))
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("baglam hesaplanamadi %s: %s", row["domain"], exc)
                with contextlib.suppress(Exception):
                    await db.execute(SAVE_SQL, row["id"], None, 0.0)
        return len(rows)

    async def run_forever(self) -> None:
        await vectors.sync_to_db()
        log.info("magaza baglam worker'i basladi (esik=%.2f)", config.STORE_CONTEXT_MIN_SCORE)
        while True:
            try:
                n = await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.error("baglam dongusu hatasi: %s", exc)
                n = 0
            await self.report()
            if n == 0:
                await asyncio.sleep(120)


async def main() -> None:
    try:
        await StoreContextWorker().run_forever()
    finally:
        await db.close()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
