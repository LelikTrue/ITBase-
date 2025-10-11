# seed_devices.py
import asyncio
import random
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для корректного импорта
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from faker import Faker
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models import Department, DeviceModel, DeviceStatus, Employee, Location
from app.schemas.asset import AssetCreate
from app.services.device_service import DeviceService

# --- НАСТРОЙКИ ---
NUMBER_OF_DEVICES = 30  # Сколько активов мы хотим создать
ADMIN_USER_ID = 1       # ID пользователя, от имени которого будут созданы активы (для лога аудита)

async def seed_devices():
    """Основная функция для генерации и добавления тестовых активов."""
    print('--- 🏁 Начало генерации тестовых активов ---')

    faker = Faker('ru_RU')
    device_service = DeviceService()

    async with AsyncSessionLocal() as db:
        # --- 1. Загружаем все справочники из БД ---
        print('📦 Загрузка справочников из базы данных...')

        device_models = (await db.execute(select(DeviceModel))).scalars().all()
        statuses = (await db.execute(select(DeviceStatus))).scalars().all()
        departments = (await db.execute(select(Department))).scalars().all()
        locations = (await db.execute(select(Location))).scalars().all()
        employees = (await db.execute(select(Employee))).scalars().all()

        # Проверка, что справочники не пустые. Если они пустые, нужно сначала запустить init_data.py
        if not all([device_models, statuses, departments, locations, employees]):
            print('\n❌ ОШИБКА: Один или несколько справочников пусты.')
            print("👉 Пожалуйста, сначала запустите скрипт 'python init_data.py' для заполнения базовых данных.")
            return

        print(f'✅ Справочники успешно загружены. Начинаем создание {NUMBER_OF_DEVICES} активов...')

        # --- 2. Цикл создания активов ---
        for i in range(NUMBER_OF_DEVICES):
            try:
                # Выбираем случайную модель и связанный с ней тип актива
                selected_model = random.choice(device_models)

                # Собираем данные для схемы AssetCreate
                # ...
                # Выбираем случайные связанные сущности, позволяя им быть None
                selected_department = random.choice(departments + [None])
                selected_employee = random.choice(employees + [None])

                asset_data = {
                    'serial_number': faker.ean(length=13),
                    'mac_address': faker.mac_address() if random.random() > 0.5 else None,
                    'notes': f'Тестовый актив №{i+1}. {faker.sentence(nb_words=10)}',
                    'asset_type_id': selected_model.asset_type_id,
                    'device_model_id': selected_model.id,
                    'status_id': random.choice(statuses).id,
                    # Теперь мы безопасно получаем .id или оставляем None
                    'department_id': selected_department.id if selected_department else None,
                    'location_id': random.choice(locations).id,
                    'employee_id': selected_employee.id if selected_employee else None,
                    'tag_ids': [],
                }

                asset_to_create = AssetCreate(**asset_data)

                # Используем наш сервис для создания актива.
                # Он сам сгенерирует инвентарный номер и создаст запись в логе аудита.
                new_device = await device_service.create_device(db, asset_to_create, user_id=ADMIN_USER_ID)

                print(f'  -> Создан актив: {new_device.inventory_number} (ID: {new_device.id})')

            except Exception as e:
                print(f'🔥 Произошла ошибка при создании актива №{i+1}: {e}')
                # Мы не прерываем цикл, чтобы скрипт попытался создать остальные активы

        print(f'\n--- 🎉 Успешно обработано {NUMBER_OF_DEVICES} активов! ---')


if __name__ == '__main__':
    # Проверяем, что скрипт запускается в асинхронном контексте
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Если цикл уже запущен (например, в Jupyter), используем await
        task = loop.create_task(seed_devices())
    else:
        # В противном случае запускаем новый цикл
        asyncio.run(seed_devices())

# --- КОНЕЦ НАСТРОЕК ---
