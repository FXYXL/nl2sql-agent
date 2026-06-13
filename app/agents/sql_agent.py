import logging
import re

from app.core.database import execute_sql, get_database_schema
from app.services.llm import chat_completion

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的 NL2SQL 助手。
根据用户提供的数据库表结构和自然语言问题，生成可执行的 SQL 语句。

规则：
1. 只返回 SQL 语句，不要返回任何解释或多余文字
2. SQL 语句不要用 markdown 代码块包裹
3. 确保 SQL 语法正确，适用于 MySQL
4. 如果问题不明确，返回最合理的查询
5. 只生成 SELECT 查询语句，不要生成任何修改数据的语句（INSERT/UPDATE/DELETE/DROP 等）
6. 使用表中实际存在的列名，不要编造列名
7. 优先使用 JOIN 而非子查询，保持 SQL 简洁
8. 聚合查询请加 GROUP BY
"""

_DANGEROUS_KEYWORDS = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|REVOKE|MERGE|EXEC|EXECUTE)\b',
    re.IGNORECASE,
)

_DANGEROUS_COMMENTS = re.compile(r'/\*.*?\*/|;--|--')


def _is_safe_sql(sql: str) -> str | None:
    if not sql:
        return "生成的 SQL 为空"
    if _DANGEROUS_COMMENTS.search(sql):
        return "拒绝执行: SQL 包含可疑注释"
    match = _DANGEROUS_KEYWORDS.search(sql)
    if match:
        return f"拒绝执行: SQL 包含危险操作 '{match.group(1)}'，仅允许 SELECT 查询"
    return None


def _extract_sql(raw: str) -> str:
    sql = raw.strip()
    match = re.search(r'```(?:sql)?\s*(.*?)\s*```', sql, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
    sql = re.sub(r'^```(?:sql)?\s*', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s*```$', '', sql, flags=re.IGNORECASE)
    return sql.strip()


async def ask(question: str) -> dict:
    schema = await get_database_schema()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"数据库表结构如下：\n\n{schema}\n\n问题：{question}",
        },
    ]

    raw_sql = await chat_completion(messages)
    sql = _extract_sql(raw_sql)
    logger.info("Generated SQL for '%s': %s", question, sql)

    safety_error = _is_safe_sql(sql)
    if safety_error:
        logger.warning("SQL rejected: %s", safety_error)
        return {
            "question": question,
            "sql": sql,
            "columns": [],
            "rows": [],
            "error": safety_error,
        }

    columns, rows = [], []
    error = None
    try:
        columns, rows = await execute_sql(sql)
    except Exception as e:
        error = str(e)
        logger.error("SQL execution failed: %s", error)

    return {
        "question": question,
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "error": error,
    }
