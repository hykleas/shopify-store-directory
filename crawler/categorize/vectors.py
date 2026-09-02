"""Embedding modeli ve nis vektorleri.

Nis vektoru = o nisin ornek basliklarinin embedding ortalamasi (L2 normalize).
Diske cache'lenir ve `niche_vectors` tablosuna yazilir; atama tamamen SQL
tarafinda pgvector ile yapilir (bkz. assign_worker.py).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import threading
from typing import Any

import numpy as np

from categorize import taxonomy
from core import config, db
from core.log import get

log = get("categorize.vectors")

CACHE_DIR = pathlib.Path(__file__).resolve().parent / ".vectors"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_model: Any = None
_model_lock = threading.Lock()


def load_model() -> Any:
    """SentenceTransformer'i tembel yukler (CPU). Sureste tek kopya."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                log.info("model yukleniyor: %s (cpu)", config.EMBED_MODEL)
                _model = SentenceTransformer(config.EMBED_MODEL, device="cpu")
                _model.max_seq_length = 96  # urun basliklari kisa; hiz icin kirp
                log.info("model hazir")
    return _model


def encode(texts: list[str], batch_size: int | None = None) -> np.ndarray:
    """L2 normalize edilmis float32 embedding matrisi dondurur."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = load_model()
    vecs = model.encode(
        texts,
        batch_size=batch_size or 64,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return np.asarray(vecs, dtype=np.float32)


def taxonomy_fingerprint() -> str:
    payload = json.dumps(taxonomy.TAXONOMY, sort_keys=True, ensure_ascii=False)
    key = config.EMBED_MODEL + "|" + payload
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _cache_path() -> pathlib.Path:
    return CACHE_DIR / ("niches_" + taxonomy_fingerprint() + ".npz")


def build_niche_vectors(force: bool = False) -> tuple[list[tuple[str, str]], np.ndarray]:
    """(kategori, nis) listesi ve karsilik gelen vektor matrisi."""
    labels = taxonomy.niches()
    cache = _cache_path()

    if cache.exists() and not force:
        data = np.load(cache, allow_pickle=False)
        matrix = data["vectors"]
        if matrix.shape[0] == len(labels):
            log.info("nis vektorleri cache'ten okundu (%d nis)", len(labels))
            return labels, matrix
        log.warning("cache boyutu uyusmuyor, yeniden hesaplaniyor")

    log.info("nis vektorleri hesaplaniyor: %s", taxonomy.summary())
    groups = taxonomy.examples()
    flat: list[str] = []
    spans: list[tuple[int, int]] = []
    for titles in groups:
        start = len(flat)
        flat.extend(titles)
        spans.append((start, len(flat)))

    all_vecs = encode(flat)
    matrix = np.zeros((len(labels), all_vecs.shape[1]), dtype=np.float32)
    for i, (start, end) in enumerate(spans):
        mean = all_vecs[start:end].mean(axis=0)
        norm = float(np.linalg.norm(mean)) or 1.0
        matrix[i] = mean / norm

    np.savez_compressed(cache, vectors=matrix)
    log.info("nis vektorleri cache'lendi: %s", cache.name)
    return labels, matrix


UPSERT_SQL = """
INSERT INTO niche_vectors (model, category, niche, embedding)
VALUES ($1, $2, $3, $4::vector)
ON CONFLICT (model, category, niche) DO UPDATE SET
  embedding = EXCLUDED.embedding,
  built_at  = now()
"""


async def sync_to_db(force: bool = False) -> int:
    """Nis vektorlerini DB'ye yazar; atama SQL tarafinda yapilacak."""
    existing = await db.fetchval(
        "SELECT count(*) FROM niche_vectors WHERE model = $1", config.EMBED_MODEL
    )
    labels = taxonomy.niches()
    if existing == len(labels) and not force:
        log.info("nis vektorleri zaten guncel (%d)", existing)
        return existing

    labels, matrix = build_niche_vectors(force=force)
    rows = [
        (config.EMBED_MODEL, cat, niche, db.vector_literal(matrix[i]))
        for i, (cat, niche) in enumerate(labels)
    ]
    await db.executemany(UPSERT_SQL, rows)
    log.info("%d nis vektoru DB'ye yazildi", len(rows))
    return len(rows)


async def main() -> None:
    try:
        await sync_to_db(force=True)
    finally:
        await db.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
