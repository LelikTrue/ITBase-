# app/db/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

class Base(DeclarativeBase):
    pass


# Создание асинхронного движка SQLAlchemy
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=10,
    connect_args={"timeout": 10},
)

# Создание фабрики сессий
# sessionmaker теперь возвращает фабрику AsyncSession
AsyncSessionFactory = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция зависимости для получения сессии базы данных.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
