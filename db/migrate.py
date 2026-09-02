#!/usr/bin/env python3
"""Numaralı .sql dosyalarını sırayla uygulayan basit migration runner.

Kullanım:
    DATABASE_URL=postgres://... python db/migrate.py           # bekleyenleri uygula
    DATABASE_URL=postgres://... python db/migrate.py --status   # durum listesi

Aynı runner hem lokal postgres'e hem Supabase'e karşı çalışır.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import re
import sys

try:
    import psycopg
except ImportError:  # pragma: no cover
    sys.exit("psycopg[binary] gerekli:  pip install 'psycopg[binary]'")

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent
FILE_RE = re.compile(r"^(\d{3,})_.+\.sql$")

BOOTSTRAP = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version     TEXT PRIMARY KEY,
  filename    TEXT NOT NULL,
  checksum    TEXT NOT NULL,
  applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def discover() -> list[tuple[str, pathlib.Path]]:
    found: list[tuple[str, pathlib.Path]] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        m = FILE_RE.match(path.name)
        if m:
            found.append((m.group(1), path))
    found.sort(key=lambda t: int(t[0]))
    return found


def checksum(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true", help="sadece durumu göster")
    ap.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = ap.parse_args()

    if not args.database_url:
        return _fail("DATABASE_URL tanımlı değil.")

    migrations = discover()
    if not migrations:
        print("Migration dosyası bulunamadı.")
        return 0

    with psycopg.connect(args.database_url, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(BOOTSTRAP)
        conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT version, checksum FROM schema_migrations")
            applied = dict(cur.fetchall())

        if args.status:
            for version, path in migrations:
                state = "applied" if version in applied else "pending"
                drift = ""
                if version in applied and applied[version] != checksum(path):
                    drift = "  ** DOSYA DEĞİŞMİŞ **"
                print(f"  {version}  {state:8}  {path.name}{drift}")
            return 0

        pending = [(v, p) for v, p in migrations if v not in applied]
        for version, path in migrations:
            if version in applied and applied[version] != checksum(path):
                print(
                    f"UYARI: {path.name} uygulandıktan sonra değişmiş. "
                    "Yeni numaralı bir migration ekleyin.",
                    file=sys.stderr,
                )

        if not pending:
            print("Bekleyen migration yok.")
            return 0

        for version, path in pending:
            sql = path.read_text(encoding="utf-8")
            print(f"-> {path.name} uygulanıyor …", flush=True)
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO schema_migrations (version, filename, checksum) "
                        "VALUES (%s, %s, %s)",
                        (version, path.name, checksum(path)),
                    )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return _fail(f"{path.name} başarısız: {exc}")
            print(f"   ok  {path.name}")

        print(f"{len(pending)} migration uygulandı.")
    return 0


def _fail(msg: str) -> int:
    print(f"HATA: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
