import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_pool():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    return _pool