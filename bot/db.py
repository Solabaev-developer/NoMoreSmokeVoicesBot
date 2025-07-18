from typing import Optional
import asyncpg

_db: Optional[asyncpg.Connection] = None

async def init_db(dsn: str):
    global _db
    _db = await asyncpg.connect(dsn)

def get_db() -> asyncpg.Connection:
    if _db is None:
        raise RuntimeError("Database is not initialized")
    return _db