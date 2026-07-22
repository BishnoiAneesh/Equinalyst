"""Shared pytest fixtures for the test suite.

`db_session` wraps each test in an outer transaction that is always rolled
back on teardown (the "join a SAVEPOINT" pattern for async SQLAlchemy). This
lets tests freely INSERT/UPDATE/DELETE against the real Dockerised Postgres
instance without leaving rows behind for other tests, or clobbering data
inserted by `scripts/seed.py`.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # A dedicated NullPool engine per test (rather than the app's pooled
    # module-level `engine` from app/db/session.py) sidesteps pytest-asyncio
    # giving each test its own event loop: pooled asyncpg connections are
    # bound to the loop that opened them, so reusing one across loops raises
    # "attached to a different loop" / "another operation is in progress".
    test_engine = create_async_engine(settings.database_url, poolclass=NullPool)

    connection = await test_engine.connect()
    trans = await connection.begin()

    session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    try:
        yield session
    finally:
        await session.close()
        # A test that triggers an IntegrityError on flush already caused
        # SQLAlchemy to auto-rollback the connection's transaction; calling
        # rollback() again here is then a harmless no-op, not an error.
        if trans.is_active:
            await trans.rollback()
        await connection.close()
        await test_engine.dispose()
