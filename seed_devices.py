# seed_devices.py
import asyncio
import random
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.database import AsyncSessionFactory
from app.models import Department, DeviceModel, DeviceStatus, Employee, Location, Tag
from app.schemas.asset import AssetCreate
from app.services.device_service import DeviceService

NUMBER_OF_DEVICES = 30
ADMIN_USER_ID = 1

async def seed_devices():
    """Основная функция для генерации и добавления тестовых активов."""
    print('--- 🏁 Начало генерации тестовых активов ---')

    faker = Faker('ru_RU')
    faker.unique.clear()

    print('📦 Загрузка справочников из базы данных...')
    async with AsyncSessionFactory() as db_for_refs:
        query = select(DeviceModel).options(joinedload(DeviceModel.asset_type))
        device_models = (await db_for_refs.execute(query)).scalars().all()
        statuses = (await db_for_refs.execute(select(DeviceStatus))).scalars().all()
        departments = (await db_for_refs.execute(select(Department))).scalars().all()
        locations = (await db_for_refs.execute(select(Location))).scalars().all()
        employees = (await db_for_refs.execute(select(Employee))).scalars().all()
        tags = (await db_for_refs.execute(select(Tag))).scalars().all()

    if not all([device_models, statuses]):
        print('\n❌ ОШИБКА: Справочники моделей или статусов пусты.')
        print("👉 Пожалуйста, сначала запустите команду 'make init-data' для заполнения базовых данных.")
        return

    print(f'✅ Справочники успешно загружены. Начинаем создание {NUMBER_OF_DEVICES} активов...')

    successful_creations = 0
    failed_creations = 0
    print("Процесс создания: ", end="", flush=True)

    for i in range(NUMBER_OF_DEVICES):
        try:
            selected_model = random.choice(device_models)
            selected_status = random.choice(statuses)
            selected_department = random.choice(departments + [None]) if departments else None
            selected_location = random.choice(locations) if locations else None
            selected_employee = random.choice(employees + [None]) if employees else None
            selected_tags = []
            if tags:
                num_tags = random.randint(0, min(3, len(tags)))
                if num_tags > 0:
                    selected_tags = random.sample(tags, num_tags)

            asset_data = {
                'name': f'{selected_model.asset_type.name} {selected_model.name}',
                'inventory_number': f'ITB-{faker.unique.random_number(digits=6, fix_len=True)}',
                'serial_number': faker.ean(length=13),
                'mac_address': faker.mac_address() if random.random() > 0.5 else None,
                'notes': f'Тестовый актив №{i+1}. {faker.sentence(nb_words=10)}',
                'asset_type_id': selected_model.asset_type_id,
                'device_model_id': selected_model.id,
                'status_id': selected_status.id,
                'department_id': selected_department.id if selected_department else None,
                'location_id': selected_location.id if selected_location else None,
                'employee_id': selected_employee.id if selected_employee else None,
                'tag_ids': [tag.id for tag in selected_tags],
            }

            asset_to_create = AssetCreate(**asset_data)

            async with AsyncSessionFactory() as db:
                device_service = DeviceService()
                await device_service.create_device(db, asset_to_create, user_id=ADMIN_USER_ID)
                print(".", end="", flush=True)
                successful_creations += 1
        except Exception as e:
            print("F", end="", flush=True)
            failed_creations += 1

    print("\n\n--- 📊 Результаты генерации ---")
    print(f"  - ✅ Успешно создано: {successful_creations}")
    print(f"  - ❌ Не удалось создать: {failed_creations}")
    print(f"  - 🔢 Всего обработано: {NUMBER_OF_DEVICES}")
    print("--- 🎉 Работа скрипта завершена! ---")

if __name__ == '__main__':
    asyncio.run(seed_devices())