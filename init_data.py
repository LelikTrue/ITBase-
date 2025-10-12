# init_data.py
import asyncio

"""
Скрипт для заполнения базы данных начальными данными
"""
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для корректного импорта
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import initial_data_storage
from app.db.database import AsyncSessionFactory, Base, async_engine
from app.models import (
    AssetType,
    Department,
    DeviceModel,
    DeviceStatus,
    Employee,
    Location,
    Manufacturer,
)


async def _seed_data(db: AsyncSession, model, data: list[dict], index_elements: list[str]):
    """
    Универсальная и производительная функция для заполнения таблиц данными.
    Использует `INSERT ... ON CONFLICT DO NOTHING` для избежания дубликатов
    на уровне базы данных, что является самым быстрым способом.
    """
    if not data:
        print(f"✔️ Нет данных для добавления в '{model.__tablename__}'.")
        return

    print(f"📦 Обработка данных для '{model.__tablename__}'...")
    stmt = insert(model).values(data)
    stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)

    await db.execute(stmt)
    # result.rowcount не всегда надежен с on_conflict, поэтому просто сообщаем об обработке
    print(f"✅ Обработано {len(data)} записей для '{model.__tablename__}'.")


async def create_tables():
    """Создает все таблицы в базе данных."""
    async with async_engine.begin() as conn:
        print('🗑️  Удаление старых таблиц...')
        await conn.run_sync(Base.metadata.drop_all)
        print('✨ Создание новых таблиц...')
        await conn.run_sync(Base.metadata.create_all)
    print('👍 Таблицы успешно созданы.')

async def main():
    """Основная функция для инициализации данных."""
    await create_tables()
    async with AsyncSessionFactory() as db:
        print('\n--- 🏁 Начало заполнения справочников ---')

        # --- Простые справочники ---
        await _seed_data(db, AssetType, initial_data_storage.ASSET_TYPES, index_elements=['name'])
        await _seed_data(db, Manufacturer, initial_data_storage.MANUFACTURERS, index_elements=['name'])
        await _seed_data(db, DeviceStatus, initial_data_storage.STATUSES, index_elements=['name'])
        await _seed_data(db, Department, initial_data_storage.DEPARTMENTS, index_elements=['name'])
        await _seed_data(db, Location, initial_data_storage.LOCATIONS, index_elements=['name'])
        await _seed_data(db, Employee, initial_data_storage.EMPLOYEES, index_elements=['employee_id'])

        # --- Сложный справочник (DeviceModel) ---
        # Сначала нужно получить ID уже созданных производителей и типов
        manufacturers = await db.execute(select(Manufacturer.id, Manufacturer.name))
        asset_types = await db.execute(select(AssetType.id, AssetType.name))

        manufacturers_map = {name: id for id, name in manufacturers}
        asset_types_map = {name: id for id, name in asset_types}

        device_models_data = initial_data_storage.get_device_models(manufacturers_map, asset_types_map)

        # Фильтруем модели, для которых не нашлись ID
        valid_device_models = [m for m in device_models_data if m['manufacturer_id'] and m['asset_type_id']]

        await _seed_data(db, DeviceModel, valid_device_models, index_elements=['name', 'manufacturer_id'])

        await db.commit()
        print('\n--- 🎉 Все данные успешно инициализированы! ---')

if __name__ == '__main__':
    asyncio.run(main())
