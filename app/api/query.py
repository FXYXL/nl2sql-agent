from fastapi import APIRouter

from app.agents.sql_agent import ask
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    result = await ask(req.question, allow_writes=req.allow_writes)
    return QueryResponse(**result)


@router.get("/health")
async def health():
    return {"status": "ok"}
