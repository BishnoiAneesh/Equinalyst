import pytest
from sqlalchemy import text

from app.db.session import AsyncSessionLocal


def test_sanity() -> None:
    """Confirms the test runner itself works."""
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_db_connection() -> None:
    """Confirms pytest-asyncio can talk to the Dockerised Postgres instance."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
