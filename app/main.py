from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.query import router as query_router
from app.core.config import validate_config
from app.core.database import engine
from app.core.logging import setup_logging
from app.services.llm import close_client

setup_logging()
validate_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await close_client()


app = FastAPI(title="NL2SQL Agent", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {type(exc).__name__}"},
    )


app.include_router(query_router)
