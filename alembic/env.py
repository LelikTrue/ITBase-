# alembic/env.py

import os
import sys
from logging.config import fileConfig
from pathlib import Path
import logging  # <-- Добавлено для работы с модулем логирования

# Добавляем корневую директорию проекта в sys.path
# Это позволяет Alembic находить модуль 'app'
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__))))


from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. Импортируем необходимые библиотеки
from dotenv import load_dotenv
import chardet  # Используем библиотеку для определения кодировки

# 2. Определяем путь к .env файлу
env_path = Path(__file__).resolve().parents[2] / ".env"

# 3. Программно определяем кодировку файла .env
detected_encoding = 'utf-8'  # Используем UTF-8 как безопасное значение по умолчанию
if env_path.exists():
    with open(env_path, 'rb') as f:  # Открываем файл в бинарном режиме
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result.get('encoding')
        confidence = result.get('confidence', 0)
        
        # Используем определенную кодировку, только если chardet достаточно уверен
        if encoding and confidence > 0.8:
            detected_encoding = encoding
        
        print(f"INFO: Detected encoding for .env is '{detected_encoding}' with confidence {confidence:.2f}")

# 4. Загружаем .env с явно указанной (определенной) кодировкой
load_dotenv(dotenv_path=env_path, encoding=detected_encoding)

# 5. Импортируем все модели, чтобы они были зарегистрированы в Base.metadata
# Это решает проблему циклических импортов при автогенерации.
# Просто импортируем пакет app.models, __init__.py сделает все остальное.
import app.models

# Теперь импортируем Base, metadata которого уже содержит все таблицы.
from app.models.base import Base


config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    # --- НАЧАЛО НОВОГО БЛОКА: ОЧИСТКА ЛОГГЕРОВ ПЕРЕД НАСТРОЙКОЙ ---
    # Получаем корневой логгер
    root_logger = logging.getLogger()
    # Удаляем все существующие обработчики из корневого логгера
    # Это предотвращает дублирование вывода, если уже были настроены какие-то дефолтные хэндлеры
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    # --- КОНЕЦ НОВОГО БЛОКА ---
    
    fileConfig(config.config_file_name)

# 6. Устанавливаем target_metadata для автогенерации
target_metadata = Base.metadata

# 7. Программно формируем и устанавливаем URL базы данных
#    Это переопределит любую настройку sqlalchemy.url из alembic.ini
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost") # 'localhost' как значение по умолчанию
DB_NAME = os.getenv("DB_NAME")

# Проверяем, что все переменные загрузились
# if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
#     raise ValueError("Не все переменные окружения для подключения к БД заданы в .env файле")

db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()