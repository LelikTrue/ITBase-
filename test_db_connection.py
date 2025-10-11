# Файл: test_db_connection.py

import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_connection():
    """
    Простой скрипт для проверки подключения к тестовой базе данных.
    """
    print('--- Начинаем проверку подключения к БД ---')

    # 1. Загружаем переменные из .env файла
    print('1. Загружаем переменные из .env...')
    load_dotenv()

    # 2. Собираем URL из отдельных переменных, как это делает основное приложение
    print('\n2. Собираем URL для подключения из переменных .env...')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    if not all([db_user, db_password, db_host, db_port, db_name]):
        print('\n[ОШИБКА] Не найдены все необходимые переменные в .env (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME).')
        return

    # Собираем основной URL и создаем тестовый
    database_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    TEST_DATABASE_URL = database_url.replace(f'/{db_name}', '/itbase_test')

    print(f'   - Основной URL (собранный): {database_url}')
    print(f'   - Сформированный тестовый URL: {TEST_DATABASE_URL}')

    # 3. Пытаемся подключиться
    print('\n2. Пытаемся создать движок SQLAlchemy...')
    try:
        engine = create_async_engine(TEST_DATABASE_URL)
        print('   - Движок успешно создан.')
    except Exception as e:
        print('\n[ОШИБКА] Не удалось создать движок SQLAlchemy.')
        print(f'Причина: {e}')
        return

    print('\n3. Пытаемся установить соединение и выполнить запрос SELECT 1...')
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT 1'))
            print(f"   - Результат запроса 'SELECT 1': {result.scalar_one()}")

        print('\n[УСПЕХ] Соединение с тестовой базой данных успешно установлено и проверено!')

    except Exception as e:
        print('\n[ОШИБКА] Не удалось подключиться к тестовой базе данных или выполнить запрос.')
        print(f'Причина: {e}')
        print('\n--- Возможные причины ---')
        print('   - Убедись, что Docker с PostgreSQL запущен.')
        print("   - Убедись, что база данных 'itbase_test' существует. Ее нужно создать вручную (один раз).")
        print('   - Проверь правильность логина/пароля/хоста/порта в твоем DATABASE_URL.')

    finally:
        await engine.dispose()
        print('\n--- Проверка завершена ---')


if __name__ == '__main__':
    # Убедимся, что база itbase_test существует.
    # В psql или DBeaver/DataGrip выполни команду: CREATE DATABASE itbase_test;
    asyncio.run(check_connection())
