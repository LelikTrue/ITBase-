# tests/conftest.py

import asyncio
from typing import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.database import get_db, Base
from app.config import settings

# --- 1. Настройка тестовой базы данных ---
TEST_DATABASE_URL = settings.DATABASE_URL_ASYNC.replace(
    f"/{settings.DB_NAME}", f"/{settings.DB_NAME}_test"
)

engine_test = create_async_engine(TEST_DATABASE_URL)
async_session_maker = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)

# --- 2. Фикстура для подготовки БД (один раз за сессию) ---
@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Создает и удаляет таблицы БД один раз за сессию."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 3. ГЛАВНОЕ РЕШЕНИЕ: Фикстура, которая управляет соединением и транзакцией ---
@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Создает соединение и транзакцию для одного теста, откатывает ее после.
    Это гарантирует 100% изоляцию.
    """
    connection = await engine_test.connect()
    transaction = await connection.begin()
    session = async_session_maker(bind=connection)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()

# --- 4. Фикстура для HTTP-клиента, которая использует ту же сессию ---
@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Создает клиент для теста, подменяя зависимость get_db
    на изолированную сессию этого теста.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    del app.dependency_overrides[get_db]