from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_db

app = FastAPI(
    title="Indian Equity Valuation API",
    description="Local-first DCF valuation tool for NSE/BSE listed companies, sourced from Screener.in",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("SELECT 1"))
    return {"status": "ok", "result": result.scalar()}
