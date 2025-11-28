# app/config.py
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Централизованная конфигурация приложения.
    Значения считываются из переменных окружения.
    """

    # --- БАЗА ДАННЫХ ---
    POSTGRES_HOST: str = Field(default="db", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(
        ..., env="POSTGRES_PASSWORD", description="Пароль для PostgreSQL (обязательный)"
    )
    POSTGRES_DB: str = Field(default="itbase", env="POSTGRES_DB")

    # --- REDIS ---
    REDIS_HOST: str = Field(default="redis", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")

    # --- БЕЗОПАСНОСТЬ ---
    SECRET_KEY: str = Field(
        ..., env="SECRET_KEY", description="Секретный ключ для JWT (обязательный)"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # --- ПУТИ ---
    TEMPLATES_DIR: Path = BASE_DIR / "templates"

    # --- URL для БД ---
    @property
    def DATABASE_URL_ASYNC(self) -> str:  # noqa: N802
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_SYNC(self) -> str:  # noqa: N802
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:  # noqa: N802
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Глобальный экземпляр
settings = Settings()
