"""asyncpg havuzu ve küçük yardımcılar. ORM yok, ham SQL."""
from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

import asyncpg

from core import config
from core.log import get

log = get("core.db")

_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()


def _dsn() -> str:
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL tanımlı değil.")
    # asyncpg 'postgres://' ve 'postgresql://' kabul eder ama Neon'un
    # '?sslmode=require&channel_binding=require' gibi ekleri libpq'ya özgü.
    dsn = config.DATABASE_URL
    for junk in ("&channel_binding=require", "?channel_binding=require"):
        dsn = dsn.replace(junk, "" if junk.startswith("&") else "?")
    return dsn.rstrip("?&")


async def pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        async with _lock:
            if _pool is None:
                _pool = await asyncpg.create_pool(
                    _dsn(),
                    min_size=1,
                    max_size=10,
                    command_timeout=60,
                    max_inactive_connection_lifetime=120,
                )
                log.info("postgres havuzu açıldı")
    return _pool


async def close() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def fetch(sql: str, *args: Any) -> list[asyncpg.Record]:
    p = await pool()
    async with p.acquire() as conn:
        return await conn.fetch(sql, *args)


async def fetchrow(sql: str, *args: Any) -> asyncpg.Record | None:
    p = await pool()
    async with p.acquire() as conn:
        return await conn.fetchrow(sql, *args)


async def fetchval(sql: str, *args: Any) -> Any:
    p = await pool()
    async with p.acquire() as conn:
        return await conn.fetchval(sql, *args)


async def execute(sql: str, *args: Any) -> str:
    p = await pool()
    async with p.acquire() as conn:
        return await conn.execute(sql, *args)


async def executemany(sql: str, rows: Sequence[Sequence[Any]]) -> None:
    if not rows:
        return
    p = await pool()
    async with p.acquire() as conn:
        await conn.executemany(sql, rows)


def vector_literal(values: Sequence[float]) -> str:
    """pgvector'ün metin gösterimi. SQL tarafında `$n::vector` ile cast edilir."""
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"
