# Path: app/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Явно загружаем переменные из .env файла, который лежит в корне проекта
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_NAME: str = os.getenv("DB_NAME")

    # Свойство для АСИНХРОННОГО URL (для FastAPI)
    @property
    def DATABASE_URL_ASYNC(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Свойство для СИНХРОННОГО URL (для Alembic)
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Остальные настройки вашего приложения
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    TEMPLATES_DIR: Path = BASE_DIR / "templates"

# Создаем единственный экземпляр настроек для всего проекта
settings = Settings()