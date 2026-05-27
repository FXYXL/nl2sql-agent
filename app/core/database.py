from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
metadata = MetaData()


async def get_database_schema() -> str:
    """异步反射数据库表结构，返回可读的 Schema 字符串。"""
    async with engine.begin() as conn:
        await conn.run_sync(metadata.reflect)

    schema_lines = []
    for table_name, table in metadata.tables.items():
        columns = [f"  - {col.name} ({col.type})" for col in table.columns]
        schema_lines.append(f"表名: {table_name}\n" + "\n".join(columns))

    return "\n\n".join(schema_lines)


async def execute_sql(sql: str) -> tuple[list[str], list[list]]:
    """执行 SQL，返回 (列名列表, 行数据列表)。"""
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        columns = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        return columns, rows
