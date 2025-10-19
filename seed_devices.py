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

from app.db.database import AsyncSessionFactory
from app.models import Department, DeviceModel, DeviceStatus, Employee, Location, Tag
from app.schemas.asset import AssetCreate
from app.services.device_service import DeviceService

# --- НАСТРОЙКИ ---
NUMBER_OF_DEVICES = 30  # Сколько активов мы хотим создать
ADMIN_USER_ID = 1       # ID пользователя, от имени которого будут созданы активы (для лога аудита)

async def seed_devices():
    """Основная функция для генерации и добавления тестовых активов."""
    print('--- 🏁 Начало генерации тестовых активов ---')

    # --- 0. Запрос подтверждения ---
    confirm = input(f"Вы уверены, что хотите создать {NUMBER_OF_DEVICES} тестовых активов? (y/n): ")
    if confirm.lower() != 'y':
        print("🚫 Операция отменена пользователем.")
        return


    faker = Faker('ru_RU')

    # --- 1. Загружаем все справочники из БД в одной сессии ---
    print('📦 Загрузка справочников из базы данных...')
    async with AsyncSessionFactory() as db_for_refs:
        device_models = (await db_for_refs.execute(select(DeviceModel))).scalars().all()
        statuses = (await db_for_refs.execute(select(DeviceStatus))).scalars().all()
        departments = (await db_for_refs.execute(select(Department))).scalars().all()
        locations = (await db_for_refs.execute(select(Location))).scalars().all()
        employees = (await db_for_refs.execute(select(Employee))).scalars().all()
        tags = (await db_for_refs.execute(select(Tag))).scalars().all()

    # Проверка, что справочники не пустые. Если они пустые, нужно сначала запустить init_data.py
    if not all([device_models, statuses, departments, locations, employees]):
        print('\n❌ ОШИБКА: Один или несколько справочников пусты.')
        print("👉 Пожалуйста, сначала запустите скрипт 'python init_data.py' для заполнения базовых данных.")
        return

    print(f'✅ Справочники успешно загружены. Начинаем создание {NUMBER_OF_DEVICES} активов...')

    # --- 2. Цикл создания активов ---    
    successful_creations = 0
    failed_creations = 0

    print("Процесс создания: ", end="", flush=True)

    for i in range(NUMBER_OF_DEVICES):
        try:
            # Выбираем случайную модель и связанный с ней тип актива
            selected_model = random.choice(device_models)
            selected_status = random.choice(statuses)

            # Собираем данные для схемы AssetCreate
            # ...
            # Выбираем случайные связанные сущности, позволяя им быть None
            selected_department = random.choice(departments + [None])
            selected_employee = random.choice(employees + [None])
            selected_tags = []
            if tags:
                num_tags = random.randint(0, 3)
                if num_tags > 0:
                    selected_tags = random.sample(tags, num_tags)

            asset_data = {
                'serial_number': faker.ean(length=13),
                'mac_address': faker.mac_address() if random.random() > 0.5 else None,
                'notes': f'Тестовый актив №{i+1}. {faker.sentence(nb_words=10)}',
                'asset_type_id': selected_model.asset_type_id,
                'device_model_id': selected_model.id,
                'status_id': selected_status.id,
                # Теперь мы безопасно получаем .id или оставляем None
                'department_id': selected_department.id if selected_department else None,
                'location_id': random.choice(locations).id,
                'employee_id': selected_employee.id if selected_employee else None,
                'tag_ids': [tag.id for tag in selected_tags],
            }

            asset_to_create = AssetCreate(**asset_data)

            # Создаем новую сессию и сервис для одной операции
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
