# Path: app/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Явно загружаем переменные из .env файла
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # --- Читаем унифицированные переменные ---
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', 'postgres')
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'itbase')

    # Свойство для АСИНХРОННОГО URL (для FastAPI)
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    # Свойство для СИНХРОННОГО URL (для Alembic и скриптов)
    @property
    def DATABASE_URL_SYNC(self) -> str:
        # psycopg2 (драйвер по умолчанию) не требует явного указания в URL
        return f'postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    # --- Остальные настройки ---
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'default_secret')
    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    TEMPLATES_DIR: Path = BASE_DIR / 'templates'

# Создаем единственный экземпляр настроек для всего проекта
settings = Settings()