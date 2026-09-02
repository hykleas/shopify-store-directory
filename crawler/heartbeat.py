"""Saatlik saglik nabzi. Web tarafinda /api/health bunu okur."""
from __future__ import annotations

import asyncio
import contextlib

from core import db, http
from core.log import get

log = get("heartbeat")

WRITE_SQL = """
INSERT INTO crawler_heartbeat (
  id, observed_at, queue_pending, domains_last_hour, products_last_hour,
  stores_total, products_total, notes
)
VALUES (1, now(), $1, $2, $3, $4, $5, $6)
ON CONFLICT (id) DO UPDATE SET
  observed_at        = EXCLUDED.observed_at,
  queue_pending      = EXCLUDED.queue_pending,
  domains_last_hour  = EXCLUDED.domains_last_hour,
  products_last_hour = EXCLUDED.products_last_hour,
  stores_total       = EXCLUDED.stores_total,
  products_total     = EXCLUDED.products_total,
  notes              = EXCLUDED.notes
"""

STATS_SQL = """
SELECT
  (SELECT count(*) FROM discovery_queue WHERE status = 'pending')::int          AS queue_pending,
  (SELECT count(*) FROM discovery_queue WHERE checked_at > now() - interval '1 hour')::int AS domains_hour,
  (SELECT count(*) FROM products WHERE first_seen_at > now() - interval '1 hour')::int     AS products_hour,
  (SELECT count(*) FROM stores WHERE NOT is_hidden)::int                        AS stores_total,
  (SELECT count(*) FROM products)::int                                          AS products_total
"""


async def write_once() -> None:
    row = await db.fetchrow(STATS_SQL)
    if row is None:
        return
    notes = "istek={requests} hata={errors} blacklist={blacklisted}".format(**http.stats)
    await db.execute(
        WRITE_SQL,
        row["queue_pending"],
        row["domains_hour"],
        row["products_hour"],
        row["stores_total"],
        row["products_total"],
        notes,
    )
    log.info(
        "nabiz: kuyruk=%s domain/saat=%s urun/saat=%s magaza=%s urun=%s",
        row["queue_pending"],
        row["domains_hour"],
        row["products_hour"],
        row["stores_total"],
        row["products_total"],
    )


async def run_forever(interval_s: int = 3600) -> None:
    while True:
        try:
            await write_once()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.error("nabiz yazilamadi: %s", exc)
        await asyncio.sleep(interval_s)


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(write_once())
