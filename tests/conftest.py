import os
import subprocess
from typing import AsyncGenerator

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
from app.models.user import User
from app.api.deps import get_current_user_from_session, get_current_superuser_from_session

# Настройка тестовой базы данных
TEST_DATABASE_URL = settings.DATABASE_URL_ASYNC.replace(
    f'/{settings.POSTGRES_DB}', f'/{settings.POSTGRES_DB}_test'
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def ensure_test_db() -> None:
    """
    Гарантирует существование тестовой базы данных и накатывает миграции.
    Запускается один раз перед всеми тестами.
    """
    # 1. Создаем базу данных если нет
    admin_url = settings.DATABASE_URL_SYNC.replace(
        f'/{settings.POSTGRES_DB}', '/postgres'
    )
    # Используем asyncpg напрямую для простых операций
    conn = await asyncpg.connect(admin_url)
    test_db_name = f'{settings.POSTGRES_DB}_test'
    try:
        db_exists = await conn.fetchval(
            'SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = $1)', test_db_name
        )
        if not db_exists:
            await conn.execute(f'CREATE DATABASE "{test_db_name}"')
    finally:
        await conn.close()

    # 2. Применяем миграции (Alembic)
    # Запускаем в синхронном subprocess, так как это разовая операция
    env = os.environ.copy()
    env['DATABASE_URL'] = TEST_DATABASE_URL

    # Пытаемся запустить миграции.
    # check=True вызовет ошибку если миграции упадут
    try:
        subprocess.run(
            ['alembic', 'upgrade', 'head'],
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,  # Скрываем лишний вывод
            stderr=subprocess.PIPE     # Но сохраняем ошибки
        )
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e.stderr.decode()}")
        raise e


@pytest_asyncio.fixture(scope="function")
async def engine_test() -> AsyncGenerator[AsyncEngine, None]:
    """
    Создает AsyncEngine для каждого теста (Scope: Function).
    Это медленнее, но гарантирует, что engine привязан к текущему event loop.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine_test: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Создает изолированную сессию БД для каждого теста.
    
    КЛЮЧЕВОЙ МОМЕНТ: Использует вложенную транзакцию (SAVEPOINT).
    Если код приложения вызовет session.commit(), это зафиксирует только SAVEPOINT,
    но не внешнюю транзакцию.
    В конце теста вызывается rollback() для внешней транзакции, отменяя ВСЕ изменения.
    """
    async with engine_test.connect() as connection:
        # 1. Начинаем внешнюю транзакцию
        transaction = await connection.begin()
        
        # 2. Создаем фабрику сессий, привязанную к ЭТОМУ соединению
        # join_transaction_mode="create_savepoint" включает режим вложенных транзакций
        session_maker = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        
        async with session_maker() as session:
            yield session
            # Сессия закрывается контекстным менеджером
            
        # 3. Откатываем внешнюю транзакцию, уничтожая все данные теста
        if transaction.is_active:
            await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
def test_app(db_session: AsyncSession) -> FastAPI:
    """
    Предоставляет экземпляр FastAPI с переопределенным get_db и авторизацией.
    """
    application = create_app()
    
    # Переопределяем зависимость get_db, чтобы она возвращала нашу тестовую сессию
    async def override_get_db():
        return db_session

    # Переопределяем авторизацию. Создаем юзера в БД, если его нет.
    async def override_get_user() -> User:
        from sqlalchemy import select

        stmt = select(User).where(User.email == "test@test.com")
        user = (await db_session.execute(stmt)).scalars().first()
        if not user:
            user = User(
                email="test@test.com",
                full_name="Test Admin",
                is_superuser=True,
                is_active=True,
                hashed_password="hashed_fake_password"  # Check field name later
            )
            db_session.add(user)
            await db_session.flush()
        return user

    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_current_user_from_session] = override_get_user
    application.dependency_overrides[get_current_superuser_from_session] = override_get_user
    
    return application


@pytest_asyncio.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Асинхронный HTTP клиент для тестов.
    """
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url='http://test',
        headers={'X-Test-Mode': 'true'},
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def test_data(db_session: AsyncSession) -> dict:
    from app.models import AssetType, Manufacturer, DeviceStatus, Location, DeviceModel, Department, Employee, User
    from app.models.tag import Tag
    from app.core.security import get_password_hash

    # Create a test user for foreign keys (e.g. ActionLog)
    # We use explicit ID=1 because many tests setup might default to user_id=1
    user = User(
        email="service_test@example.com",
        full_name="Service Test User",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_superuser=True
    )
    # Note: We can't easily force ID=1 in Postgres without raw SQL if sequence is used, 
    # but for fresh DB it's likely 1. 
    # Instead of relying on ID=1, we should return this user and use its ID in tests.
    
    asset_type = AssetType(name='Компьютер', prefix='PC', slug='computer')
    manufacturer = Manufacturer(name='TestCorp')
    status = DeviceStatus(name='Активен', slug='active')
    location = Location(name='Тестовая локация', slug='test-location')
    department = Department(name='IT Dept', slug='it-dept')
    tag = Tag(name='Test Tag')

    db_session.add_all([user, asset_type, manufacturer, status, location, department, tag])
    await db_session.flush()

    device_model = DeviceModel(
        name='TestModel 9000',
        manufacturer_id=manufacturer.id,
        asset_type_id=asset_type.id,
    )
    employee = Employee(
        last_name='Ivanov',
        first_name='Ivan',
        patronymic='Ivanovich'
    )

    db_session.add(device_model)
    db_session.add(employee)
    await db_session.flush()

    return {
        'user': user,
        'asset_type': asset_type,
        'manufacturer': manufacturer,
        'status': status,
        'location': location,
        'department': department,
        'device_model': device_model,
        'employee': employee,
        'tag': tag
    }
