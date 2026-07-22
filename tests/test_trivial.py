import pytest
from sqlalchemy import text


def test_sanity() -> None:
    """Confirms the test runner itself works."""
    assert 1 + 1 == 2


@pytest.mark.asyncio
async def test_db_connection(db_session) -> None:
    """Confirms pytest-asyncio can talk to the Dockerised Postgres instance.

    Uses the `db_session` fixture (tests/conftest.py) rather than the app's
    pooled `AsyncSessionLocal` directly -- see conftest.py's docstring for why
    a pooled engine's connections can't safely cross pytest-asyncio's
    per-test event loops.
    """
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1