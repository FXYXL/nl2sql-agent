from fastapi import FastAPI

from app.api.query import router as query_router
from app.core.database import engine

app = FastAPI(title="NL2SQL Agent")
app.include_router(query_router)


@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
