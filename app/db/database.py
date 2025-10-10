# Path: app/db/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings  # <-- Импортируем из нашего нового конфига

# Создаем асинхронный движок, используя готовый URL
async_engine = create_async_engine(settings.DATABASE_URL_ASYNC)

# Фабрика для асинхронных сессий
AsyncSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, autocommit=False, autoflush=False, expire_on_commit=False
)

# Ваша базовая модель, которую используют все остальные модели
Base = declarative_base()

# Асинхронная зависимость для получения сессии БД в эндпоинтах
async def get_db() -> AsyncSession:
    """
    Зависимость для получения сессии БД.
    В тестах эта функция будет подменена, чтобы использовать тестовую сессию.
    В реальном приложении она создает новую сессию для каждого запроса.
    """
    session = AsyncSessionLocal()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()