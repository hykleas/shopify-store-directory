"""Gunluk bakim gorevleri (APScheduler).

  03:10 UTC  daily_rollup      - gunluk katalog aktivitesi ozeti
  04:00 UTC  product_spread    - gorsel hash + eslestirme + yayilim
  05:00 UTC  prune             - 30 gunden eski not_shopify kayitlarini sil
"""
from __future__ import annotations

import asyncio
import contextlib

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from activity import daily_rollup, product_spread
from core import db
from core.log import get

log = get("scheduler")

PRUNE_QUEUE_SQL = """
DELETE FROM discovery_queue
WHERE status IN ('not_shopify', 'error')
  AND checked_at < now() - interval '30 days'
"""

RESET_STUCK_SQL = """
UPDATE discovery_queue
SET status = 'pending'
WHERE status = 'checking' AND created_at < now() - interval '1 hour'
"""


async def _safe(name: str, coro_fn) -> None:
    try:
        log.info("gorev basladi: %s", name)
        result = await coro_fn()
        log.info("gorev bitti: %s %s", name, result if result is not None else "")
    except Exception as exc:  # noqa: BLE001
        log.error("gorev basarisiz %s: %s", name, exc)


async def prune() -> str:
    removed = await db.execute(PRUNE_QUEUE_SQL)
    await db.execute(RESET_STUCK_SQL)
    return removed


def build() -> AsyncIOScheduler:
    sched = AsyncIOScheduler(timezone="UTC")
    sched.add_job(
        lambda: asyncio.create_task(_safe("daily_rollup", daily_rollup.run)),
        "cron", hour=3, minute=10, id="daily_rollup", misfire_grace_time=3600,
    )
    sched.add_job(
        lambda: asyncio.create_task(_safe("product_spread", product_spread.run)),
        "cron", hour=4, minute=0, id="product_spread", misfire_grace_time=3600,
    )
    sched.add_job(
        lambda: asyncio.create_task(_safe("prune", prune)),
        "cron", hour=5, minute=0, id="prune", misfire_grace_time=3600,
    )
    return sched


async def run_forever() -> None:
    sched = build()
    sched.start()
    log.info("zamanlayici acik: %s", ", ".join(j.id for j in sched.get_jobs()))
    forever = asyncio.Event()
    try:
        await forever.wait()
    finally:
        sched.shutdown(wait=False)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_forever())
