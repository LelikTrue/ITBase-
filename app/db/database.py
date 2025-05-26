# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv # Убедитесь, что этот импорт есть

# Загружаем переменные окружения, если скрипт запускается напрямую (вне Docker Compose)
load_dotenv()

# Получаем отдельные компоненты URL из переменных окружения
# Если DB_HOST не установлен, используем 'db' по умолчанию (имя сервиса БД в Docker Compose)
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Формируем DATABASE_URL из полученных переменных
# Оборонительная проверка, чтобы приложение падало с понятной ошибкой, если переменные не установлены
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    raise ValueError(
        "One or more database environment variables (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD) are not set!"
        " Please check your .env file and docker-compose.yml"
    )

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()