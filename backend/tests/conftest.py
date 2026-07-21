import asyncio
import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from database.base import Base

TEST_DATABASE_URL = settings.TEST_DATABASE_URL
ADMIN_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"
_TEST_DB_NAME = TEST_DATABASE_URL.rsplit("/", 1)[-1]


def _database_available() -> bool:
    """Return True if PostgreSQL is reachable on localhost:5432."""

    async def _try_connect() -> bool:
        try:
            conn = await asyncpg.connect(
                user="postgres", password="postgres", host="localhost", port=5432, database="postgres", timeout=2
            )
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.run(_try_connect())


async def _ensure_test_db() -> None:
    """Create the test database if it does not exist."""
    conn = await asyncpg.connect(user="postgres", password="postgres", host="localhost", port=5432, database="postgres")
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", _TEST_DB_NAME)
    if not exists:
        await conn.execute(f'CREATE DATABASE "{_TEST_DB_NAME}"')
    await conn.close()


async def _drop_test_db() -> None:
    """Drop the test database."""
    conn = await asyncpg.connect(user="postgres", password="postgres", host="localhost", port=5432, database="postgres")
    await conn.execute(f'DROP DATABASE IF EXISTS "{_TEST_DB_NAME}"')
    await conn.close()


@pytest.fixture(scope="session")
def db_available() -> bool:
    available = _database_available()
    if not available:
        pytest.skip("PostgreSQL not available on localhost:5432")
    return True


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def ensure_db(db_available: bool) -> AsyncGenerator[None, None]:
    """Create test database once per session, drop on teardown."""
    if db_available:
        await _ensure_test_db()
        yield
        with contextlib.suppress(Exception):
            await _drop_test_db()
    else:
        yield


@pytest_asyncio.fixture
async def engine(ensure_db: None):
    """Async engine connected to the test database. Creates tables before each test, drops after."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, Any]:
    """Read-committed session without autoflush for testing model/repo behaviour."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, Any]:
    """Session that commits on success, rolls back on failure. Suitable for service-level tests."""
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
