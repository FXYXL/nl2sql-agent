from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    allow_writes: bool = False


class QueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str] = []
    rows: list[list] = []
    error: str | None = None
    is_write: bool = False
    affected_rows: int = 0
