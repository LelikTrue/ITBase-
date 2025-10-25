from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi import FastAPI

from app.config import settings
from app.db.database import Base, get_db
from app.main import create_app # Импортируем ФАБРИКУ, а не готовый app

# Настройка тестовой базы данных
TEST_DATABASE_URL = settings.DATABASE_URL_ASYNC.replace(
    f'/{settings.DB_NAME}', f'/{settings.DB_NAME}_test'
)

engine_test = create_async_engine(TEST_DATABASE_URL)
async_session_maker = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)

# Фикстура для подготовки БД (один раз за сессию)
@pytest_asyncio.fixture(scope='session', autouse=True)
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Фикстура для сессии
@pytest_asyncio.fixture(scope='function')
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    connection = await engine_test.connect()
    transaction = await connection.begin()
    session = async_session_maker(bind=connection)
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()

# Фикстура для создания ИЗОЛИРОВАННОГО приложения
@pytest_asyncio.fixture(scope="function")
def test_app(db_session: AsyncSession) -> FastAPI:
    app = create_app() # Создаем чистый экземпляр только для этого теста
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    return app

# Фикстура клиента теперь использует изолированное приложение
@pytest_asyncio.fixture(scope='function')
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=test_app, base_url='http://test') as client:
        yield client