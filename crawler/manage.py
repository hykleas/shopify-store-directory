#!/usr/bin/env python3
"""Operasyon komutlari.

  python manage.py stats
  python manage.py hide-store example.com          # kaldirma talebi
  python manage.py unhide-store example.com
  python manage.py recrawl example.com             # siraya al
  python manage.py seed domains.txt                # elle domain ekle
  python manage.py removals                        # bekleyen kaldirma talepleri
  python manage.py resolve-removal 12              # talebi isle + magazayi gizle
  python manage.py rebuild-niches                  # nis vektorlerini yeniden kur
"""
from __future__ import annotations

import argparse
import asyncio
import pathlib
import sys

from core import db
from core.log import get

log = get("manage")


async def cmd_stats() -> int:
    row = await db.fetchrow(
        """
        SELECT
          (SELECT count(*) FROM discovery_queue)                                  AS queue_total,
          (SELECT count(*) FROM discovery_queue WHERE status='pending')           AS queue_pending,
          (SELECT count(*) FROM discovery_queue WHERE status='shopify')           AS queue_shopify,
          (SELECT count(*) FROM discovery_queue WHERE status='not_shopify')       AS queue_not,
          (SELECT count(*) FROM discovery_queue WHERE status='error')             AS queue_error,
          (SELECT count(*) FROM stores)                                           AS stores,
          (SELECT count(*) FROM stores WHERE is_hidden)                           AS stores_hidden,
          (SELECT count(*) FROM stores WHERE NOT is_active)                       AS stores_inactive,
          (SELECT count(*) FROM stores WHERE last_crawled_at IS NOT NULL)         AS stores_crawled,
          (SELECT count(*) FROM products)                                         AS products,
          (SELECT count(*) FROM products WHERE embedding IS NULL)                 AS products_unembedded,
          (SELECT count(*) FROM products WHERE category = 'uncategorized')        AS products_uncat,
          (SELECT count(*) FROM products WHERE category IS NULL)                  AS products_unassigned,
          (SELECT count(*) FROM variants)                                         AS variants,
          (SELECT count(*) FROM product_matches)                                  AS matches,
          (SELECT count(*) FROM removal_requests WHERE status='pending')          AS removals_pending
        """
    )
    hb = await db.fetchrow("SELECT * FROM crawler_heartbeat WHERE id = 1")

    print("--- kuyruk ---")
    print(f"  toplam        {row['queue_total']}")
    print(f"  bekleyen      {row['queue_pending']}")
    print(f"  shopify       {row['queue_shopify']}")
    print(f"  shopify degil {row['queue_not']}")
    print(f"  hata          {row['queue_error']}")
    print("--- magazalar ---")
    print(f"  toplam        {row['stores']}")
    print(f"  crawl edilmis {row['stores_crawled']}")
    print(f"  gizli         {row['stores_hidden']}")
    print(f"  pasif         {row['stores_inactive']}")
    print("--- urunler ---")
    print(f"  toplam        {row['products']}")
    print(f"  varyant       {row['variants']}")
    print(f"  embed bekleyen{row['products_unembedded']:>7}")
    print(f"  atama bekleyen{row['products_unassigned']:>7}")
    print(f"  uncategorized {row['products_uncat']}")
    print(f"  eslesme       {row['matches']}")
    print("--- talepler ---")
    print(f"  bekleyen kaldirma {row['removals_pending']}")
    if hb:
        print("--- nabiz ---")
        print(f"  son yazim     {hb['observed_at']}")
        print(f"  domain/saat   {hb['domains_last_hour']}")
        print(f"  urun/saat     {hb['products_last_hour']}")
        print(f"  not           {hb['notes']}")
    else:
        print("--- nabiz ---\n  henuz yazilmadi")
    return 0


async def cmd_hide(domain: str, hidden: bool) -> int:
    row = await db.fetchrow(
        "UPDATE stores SET is_hidden = $2 WHERE domain = $1 RETURNING id, domain",
        domain.strip().lower(),
        hidden,
    )
    if row is None:
        print(f"bulunamadi: {domain}", file=sys.stderr)
        return 1
    print(f"{row['domain']} -> is_hidden={hidden}")
    return 0


async def cmd_recrawl(domain: str) -> int:
    row = await db.fetchrow(
        "UPDATE stores SET last_crawled_at = NULL, crawl_priority = 1, "
        "is_active = true, fail_count = 0 WHERE domain = $1 RETURNING domain",
        domain.strip().lower(),
    )
    if row is None:
        print(f"bulunamadi: {domain}", file=sys.stderr)
        return 1
    print(f"{row['domain']} siraya alindi (priority 1)")
    return 0


async def cmd_seed(path: str) -> int:
    from discovery.domain_filter import normalize

    file = pathlib.Path(path)
    if not file.exists():
        print(f"dosya yok: {path}", file=sys.stderr)
        return 1
    raw = [ln.strip() for ln in file.read_text(encoding="utf-8").splitlines()]
    domains = sorted({d for d in (normalize(r) for r in raw if r) if d})
    if not domains:
        print("gecerli domain bulunamadi", file=sys.stderr)
        return 1
    await db.execute(
        "INSERT INTO discovery_queue (domain, source) "
        "SELECT unnest($1::text[]), 'manual' ON CONFLICT (domain) DO NOTHING",
        domains,
    )
    print(f"{len(domains)} domain kuyruga eklendi")
    return 0


async def cmd_removals() -> int:
    rows = await db.fetch(
        "SELECT id, domain, email, reason, created_at FROM removal_requests "
        "WHERE status = 'pending' ORDER BY created_at"
    )
    if not rows:
        print("bekleyen talep yok")
        return 0
    for r in rows:
        print(f"#{r['id']}  {r['domain']:<40} {r['created_at']:%Y-%m-%d}  {(r['reason'] or '')[:60]}")
    print(f"\n{len(rows)} talep. Islemek icin: python manage.py resolve-removal <id>")
    return 0


async def cmd_resolve_removal(request_id: int) -> int:
    row = await db.fetchrow(
        "UPDATE removal_requests SET status = 'done' WHERE id = $1 RETURNING domain",
        request_id,
    )
    if row is None:
        print(f"talep bulunamadi: {request_id}", file=sys.stderr)
        return 1
    await db.execute(
        "UPDATE stores SET is_hidden = true WHERE domain = $1", row["domain"].lower()
    )
    print(f"#{request_id} islendi, {row['domain']} gizlendi")
    return 0


async def cmd_rebuild_niches() -> int:
    from categorize import vectors

    n = await vectors.sync_to_db(force=True)
    await db.execute("UPDATE products SET category = NULL, niche = NULL")
    print(f"{n} nis vektoru yenilendi; tum urunler yeniden atanacak")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Crawler operasyon komutlari")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    for name in ("hide-store", "unhide-store", "recrawl"):
        sub.add_parser(name).add_argument("domain")
    sub.add_parser("seed").add_argument("file")
    sub.add_parser("removals")
    sub.add_parser("resolve-removal").add_argument("id", type=int)
    sub.add_parser("rebuild-niches")
    return ap


async def dispatch(args: argparse.Namespace) -> int:
    try:
        match args.cmd:
            case "stats":
                return await cmd_stats()
            case "hide-store":
                return await cmd_hide(args.domain, True)
            case "unhide-store":
                return await cmd_hide(args.domain, False)
            case "recrawl":
                return await cmd_recrawl(args.domain)
            case "seed":
                return await cmd_seed(args.file)
            case "removals":
                return await cmd_removals()
            case "resolve-removal":
                return await cmd_resolve_removal(args.id)
            case "rebuild-niches":
                return await cmd_rebuild_niches()
            case _:
                return 1
    finally:
        await db.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(dispatch(build_parser().parse_args())))
