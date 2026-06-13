import asyncio
import logging
from time import time

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import DATABASE_URL, MAX_SQL_ROWS

logger = logging.getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False)
metadata = MetaData()

_cached_schema: str | None = None
_cache_timestamp: float = 0.0
_cache_ttl_seconds = 300
_cache_lock = asyncio.Lock()


def _is_cache_valid() -> bool:
    return _cached_schema is not None and (time() - _cache_timestamp) < _cache_ttl_seconds


def invalidate_schema_cache():
    global _cached_schema, _cache_timestamp
    _cached_schema = None
    _cache_timestamp = 0.0


async def get_database_schema() -> str:
    global _cached_schema, _cache_timestamp

    if _is_cache_valid():
        return _cached_schema  # type: ignore[return-value]

    async with _cache_lock:
        if _is_cache_valid():
            return _cached_schema  # type: ignore[return-value]
        logger.info("Reflecting database schema...")
        async with engine.begin() as conn:
            await conn.run_sync(metadata.reflect)

        schema_lines = []
        for table_name, table in metadata.tables.items():
            columns = [f"  - {col.name} ({col.type})" for col in table.columns]
            schema_lines.append(f"表名: {table_name}\n" + "\n".join(columns))

        _cached_schema = "\n\n".join(schema_lines)
        _cache_timestamp = time()
        logger.info("Schema cached (%d tables)", len(metadata.tables))
        return _cached_schema


async def execute_sql(sql: str) -> tuple[list[str], list[list]]:
    limited_sql = sql.rstrip().rstrip(";")
    limited_sql = f"SELECT * FROM ({limited_sql}) AS _sub LIMIT {MAX_SQL_ROWS}"

    logger.info("Executing SQL: %s", limited_sql[:500])
    async with engine.connect() as conn:
        result = await conn.execute(text(limited_sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        logger.info("Query returned %d rows", len(rows))
        return columns, rows
