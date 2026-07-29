import asyncio
import logging
import re
from time import time

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import DATABASE_URL, MAX_SQL_ROWS, QUERY_TIMEOUT

logger = logging.getLogger(__name__)

engine = create_async_engine(DATABASE_URL, echo=False)
metadata = MetaData()

_cached_schema: str | None = None
_cache_timestamp: float = 0.0
_cache_ttl_seconds = 300
_cache_lock = asyncio.Lock()

# 统一的写操作检测正则，sql_agent.py 也复用此定义
WRITE_PATTERN = re.compile(
    r'^\s*(INSERT|UPDATE|DELETE|REPLACE|CALL)\b',
    re.IGNORECASE,
)


def is_write_sql(sql: str) -> bool:
    """判断 SQL 是否为写操作（INSERT/UPDATE/DELETE/REPLACE/CALL）"""
    return bool(WRITE_PATTERN.match(sql.strip()))


def _is_cache_valid() -> bool:
    return _cached_schema is not None and (time() - _cache_timestamp) < _cache_ttl_seconds


def invalidate_schema_cache():
    """清除 schema 缓存和 metadata，切换数据库时必须调用"""
    global _cached_schema, _cache_timestamp
    _cached_schema = None
    _cache_timestamp = 0.0
    metadata.clear()  # 清理旧库的表结构，避免新旧库表混在一起


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
    clean_sql = sql.strip().rstrip(";")
    is_write = is_write_sql(clean_sql)

    logger.info("Executing SQL: %s", clean_sql[:500])

    async def _execute() -> tuple[list[str], list[list]]:
        async with engine.connect() as conn:
            if is_write:
                result = await conn.execute(text(clean_sql))
                await conn.commit()
                affected = result.rowcount
                return ["affected_rows"], [[affected]]
            else:
                exec_sql = _inject_limit(clean_sql, MAX_SQL_ROWS)
                result = await conn.execute(text(exec_sql))
                columns = list(result.keys())
                rows = [list(row) for row in result.fetchall()]
                logger.info("Query returned %d rows", len(rows))
                return columns, rows

    try:
        return await asyncio.wait_for(_execute(), timeout=QUERY_TIMEOUT)
    except asyncio.TimeoutError:
        raise RuntimeError(f"Query timed out after {QUERY_TIMEOUT}s")


_LIMIT_TAIL_PATTERN = re.compile(r'\blimit\s+\d+\s*$', re.IGNORECASE)


def _inject_limit(sql: str, max_rows: int) -> str:
    """对 SELECT 语句注入 LIMIT，已有 LIMIT 则不重复添加"""
    if _LIMIT_TAIL_PATTERN.search(sql):
        return sql
    return f"{sql} LIMIT {max_rows}"
