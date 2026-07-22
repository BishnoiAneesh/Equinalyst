from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Nothing to warm up yet -- engine connections are lazy. Placeholder kept
    # so later sprints (e.g. startup cache warm, scheduler ping) have a home.
    yield


app = FastAPI(
    title="Indian Equity Valuation Tool",
    description=(
        "Local-first DCF valuation for NSE/BSE listed companies, "
        "sourced from Screener.in."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Liveness check -- process is up, no dependency checks."""
    return {
        "status": "ok",
        "env": settings.app_env,
    }


@app.get("/health/db", tags=["health"])
async def health_db(
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    """Readiness check -- confirms the app can round-trip a query to Postgres."""
    result = await db.execute(text("SELECT 1"))
    value = result.scalar_one()
    return {
        "status": "ok",
        "result": value,
    }