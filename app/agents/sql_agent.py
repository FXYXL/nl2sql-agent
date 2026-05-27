import json
import re

from app.core.database import execute_sql, get_database_schema
from app.services.llm import chat_completion

SYSTEM_PROMPT = """你是一个专业的 NL2SQL 助手。
根据用户提供的数据库表结构和自然语言问题，生成可执行的 SQL 语句。

规则：
1. 只返回 SQL 语句，不要返回任何解释或多余文字
2. SQL 语句不要用 markdown 代码块包裹
3. 确保 SQL 语法正确，适用于 MySQL
4. 如果问题不明确，返回最合理的查询
"""


async def ask(question: str) -> dict:
    """接收自然语言问题，返回 SQL 和查询结果。"""
    schema = await get_database_schema()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"数据库表结构如下：\n\n{schema}\n\n问题：{question}",
        },
    ]

    sql = await chat_completion(messages)
    sql = sql.strip()
    # 去除可能的 markdown 代码块标记
    sql = re.sub(r"^```(?:sql)?\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip()

    columns, rows = [], []
    error = None
    try:
        columns, rows = await execute_sql(sql)
    except Exception as e:
        error = str(e)

    return {
        "question": question,
        "sql": sql,
        "columns": columns,
        "rows": rows,
        "error": error,
    }
