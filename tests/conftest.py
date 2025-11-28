# tests/conftest.py
import os
import subprocess
from collections.abc import AsyncGenerator

import asyncpg
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.config import settings
from app.db.database import get_db
from app.main import create_app

# Настройка тестовой базы данных
TEST_DATABASE_URL = settings.DATABASE_URL_ASYNC.replace(
    f"/{settings.POSTGRES_DB}", f"/{settings.POSTGRES_DB}_test"
)


@pytest_asyncio.fixture(scope="function")
async def engine_test() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine_test: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    connection = await engine_test.connect()
    transaction = await connection.begin()
    session_maker = async_sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False
    )
    session = session_maker()
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope="function")
def test_app(db_session: AsyncSession) -> FastAPI:
    application = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-Test-Mode": "true"},  # Пропускаем auth middleware в тестах
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def ensure_test_db():
    # Connect to the default 'postgres' database to create the test DB if it doesn't exist
    admin_url = settings.DATABASE_URL_SYNC.replace(
        f"/{settings.POSTGRES_DB}", "/postgres"
    )
    conn = await asyncpg.connect(admin_url)
    test_db_name = f"{settings.POSTGRES_DB}_test"
    try:
        db_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = $1)", test_db_name
        )
        if not db_exists:
            await conn.execute(f'CREATE DATABASE "{test_db_name}"')
    finally:
        await conn.close()

    # Apply Alembic migrations to the test database
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    subprocess.run(["alembic", "upgrade", "head"], env=env, check=True)
