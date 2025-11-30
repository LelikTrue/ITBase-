import asyncio
import random
import sys
from datetime import date, timedelta
from pathlib import Path

from faker import Faker
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

# Настройка путей
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from app.core.security import get_password_hash
from app.db.database import AsyncSessionFactory
from app.models import (
    AssetType,
    Department,
    DeviceModel,
    DeviceStatus,
    Employee,
    Location,
    Tag,
    User,
)
from app.schemas.asset import AssetCreate
from app.services.device_service import DeviceService

# ID администратора для логов
ADMIN_USER_ID = 1

# --- СЦЕНАРИИ ГЕНЕРАЦИИ (Ваша реальность) ---
SCENARIOS = [
    # 1. IP Телефония (Fanvil)
    {
        "name": "IP Телефоны",
        "count": 13,
        "type_hint": ["IP-телефон", "Телефон", "Сетевое оборудование", "Периферия"],
        "brand_hint": "Fanvil",
        "model_name": "X3U / X4U",
        "price_range": (3000, 7000),
        "date_range": ("-3y", "-1y"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 5
    },
    # 2. Мобильные (Samsung)
    {
        "name": "Корпоративные мобильные",
        "count": 22,
        "type_hint": ["Смартфон", "Телефон", "Периферия"],
        "brand_hint": "Samsung",
        "model_name": "Galaxy A52 / S21",
        "price_range": (15000, 45000),
        "date_range": ("-2y", "today"),
        "status_dist": {"В эксплуатации": 0.9, "В резерве": 0.05, "На ремонте": 0.05},
        "lifespan": 3
    },
    # 3. Топовые ПК (Дорогие)
    {
        "name": "Рабочие станции (TOP)",
        "count": 4,
        "type_hint": ["ПК", "Компьютер", "Рабочая станция"],
        "brand_hint": "Dell",
        "model_name": "Precision / Custom Build i9",
        "price_range": (60000, 150000),
        "date_range": ("-1y", "today"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 5
    },
    # 4. Старые ПК (DDR3, 2021 год)
    {
        "name": "Офисные ПК (Legacy)",
        "count": 50,
        "type_hint": ["ПК", "Компьютер"],
        "brand_hint": "HP",
        "model_name": "ProDesk 400 G1 (Old)",
        "price_range": (5000, 12000),
        "date_range": ("2021-01-01", "2021-12-31"),
        "status_dist": {"В эксплуатации": 0.85, "На складе": 0.05, "Списан": 0.1},
        "notes_prefix": "Legacy DDR3. Требует замены.",
        "lifespan": 5
    },
    # 5. Мониторы
    {
        "name": "Мониторы",
        "count": 55,
        "type_hint": ["Монитор", "Периферия"],
        "brand_hint": "Dell",
        "model_name": "24 Monitor",
        "price_range": (5000, 15000),
        "date_range": ("-4y", "-1y"),
        "status_dist": {"В эксплуатации": 0.9, "На складе": 0.1},
        "lifespan": 7
    },
    # 6. Свичи Keenetic (В работе)
    {
        "name": "Свичи Keenetic",
        "count": 15,
        "type_hint": ["Сетевое оборудование", "Коммутатор"],
        "brand_hint": "Keenetic",
        "model_name": "Speedster / Giga",
        "price_range": (4000, 8000),
        "date_range": ("-2y", "-6m"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 6
    },
    # 7. Свичи TP-Link (На складе)
    {
        "name": "Свичи TP-Link L3 (Резерв)",
        "count": 10,
        "type_hint": ["Сетевое оборудование", "Коммутатор"],
        "brand_hint": "TP-Link",
        "model_name": "JetStream L3",
        "price_range": (12000, 25000),
        "date_range": ("-3m", "today"),
        "status_dist": {"На складе": 1.0},
        "lifespan": 8
    },
    # 8. Телевизоры
    {
        "name": "ТВ панели",
        "count": 6,
        "type_hint": ["Телевизор", "Монитор", "Периферия"],
        "brand_hint": "LG",
        "model_name": "50-inch 4K",
        "price_range": (25000, 50000),
        "date_range": ("-3y", "-1y"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 7
    },
    # 9. Плоттер (Один дорогой)
    {
        "name": "Плоттер A0",
        "count": 1,
        "type_hint": ["Принтер", "Периферия"],
        "brand_hint": "Epson",
        "model_name": "SureColor T-Series",
        "price_range": (145000, 155000),
        "date_range": ("-2y", "-1y"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 7
    },
    # 10. Обычные принтеры
    {
        "name": "МФУ офисные",
        "count": 10,
        "type_hint": ["Принтер", "Периферия"],
        "brand_hint": "Kyocera",
        "model_name": "ECOSYS",
        "price_range": (15000, 35000),
        "date_range": ("-3y", "-1y"),
        "status_dist": {"В эксплуатации": 0.9, "На ремонте": 0.1},
        "lifespan": 5
    },
    # 11. Камеры
    {
        "name": "Видеонаблюдение",
        "count": 25,
        "type_hint": ["Камера", "Периферия", "Сетевое оборудование"],
        "brand_hint": "Dahua",
        "model_name": "IPC-HFW",
        "price_range": (4000, 6000),
        "date_range": ("-2y", "-1y"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 5
    },
    # 12. Серверы
    {
        "name": "Серверная стойка",
        "count": 3,
        "type_hint": ["Сервер", "ПК"],
        "brand_hint": "HP",
        "model_name": "ProLiant DL360",
        "price_range": (200000, 500000),
        "date_range": ("-4y", "-2y"),
        "status_dist": {"В эксплуатации": 1.0},
        "lifespan": 7
    }
]

async def ensure_admin_exists(db):
    """Проверяет существование админа и создает его при необходимости."""
    print("👤 Проверка существования администратора...")
    result = await db.execute(select(User).where(User.id == ADMIN_USER_ID))
    admin = result.scalars().first()

    if not admin:
        print(f"⚠️ Администратор (ID={ADMIN_USER_ID}) не найден. Создаем технического пользователя...")
        admin = User(
            id=ADMIN_USER_ID,
            email="admin@example.com",
            hashed_password=get_password_hash("admin"),
            full_name="System Admin",
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        await db.commit()
        # Обновляем последовательность ID, чтобы следующий созданный пользователь получил ID=2
        await db.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));"))
        await db.commit()
        print("✅ Администратор создан (admin@example.com / admin).")
    else:
        print("✅ Администратор найден.")

async def seed_devices():
    print('--- 🏭 Начало генерации активов по сценарию компании ---')
    faker = Faker('ru_RU')
    faker.unique.clear()

    async with AsyncSessionFactory() as db:
        # 0. Гарантируем наличие пользователя для логов
        await ensure_admin_exists(db)

        # 1. Загрузка справочников
        all_types = (await db.execute(select(AssetType))).scalars().all()
        all_models = (await db.execute(select(DeviceModel).options(joinedload(DeviceModel.manufacturer)))).scalars().all()
        all_statuses = (await db.execute(select(DeviceStatus))).scalars().all()
        all_depts = (await db.execute(select(Department))).scalars().all()
        all_locs = (await db.execute(select(Location))).scalars().all()
        all_emps = (await db.execute(select(Employee))).scalars().all()
        all_tags = (await db.execute(select(Tag))).scalars().all()

        if not all_types or not all_statuses:
            print("❌ ОШИБКА: Справочники пусты. Запустите 'make init-data'")
            return

        service = DeviceService()
        total_created = 0

        # Хелпер для поиска статуса по имени
        status_map = {s.name: s for s in all_statuses}

        # --- ЗАПУСК СЦЕНАРИЕВ ---
        for scenario in SCENARIOS:
            print(f"\n⚙️  Партия: {scenario['name']} ({scenario['count']} шт.)")

            # 1. Определяем Тип Актива
            target_type = None
            for hint in scenario['type_hint']:
                target_type = next((t for t in all_types if hint.lower() in t.name.lower()), None)
                if target_type: break

            if not target_type:
                target_type = all_types[0]
                print(f"   ⚠️ Тип '{scenario['type_hint'][0]}' не найден, используем '{target_type.name}'")

            # 2. Ищем подходящую модель
            suitable_models = [
                m for m in all_models
                if m.asset_type_id == target_type.id
                and (scenario['brand_hint'].lower() in m.manufacturer.name.lower() if m.manufacturer else True)
            ]

            if not suitable_models:
                suitable_models = [m for m in all_models if m.asset_type_id == target_type.id]

            if not suitable_models:
                suitable_models = all_models

            # 3. Генерация
            batch_created = 0
            for _ in range(scenario['count']):
                try:
                    model = random.choice(suitable_models)

                    # Даты
                    if "2021" in str(scenario['date_range']):
                        purchase_date = faker.date_between(start_date=date(2021, 1, 1), end_date=date(2021, 12, 31))
                    else:
                        purchase_date = faker.date_between(start_date=scenario['date_range'][0], end_date=scenario['date_range'][1])

                    warranty_end = purchase_date + timedelta(days=365 * random.choice([1, 2, 3]))
                    price = random.uniform(scenario['price_range'][0], scenario['price_range'][1])

                    lifespan_days = scenario['lifespan'] * 365
                    days_used = (date.today() - purchase_date).days
                    wear = (days_used / lifespan_days) * 100
                    wear += random.uniform(-5, 10)
                    wear = max(0, min(100, wear))

                    status_names = list(scenario['status_dist'].keys())
                    status_weights = list(scenario['status_dist'].values())
                    chosen_status_name = random.choices(status_names, weights=status_weights, k=1)[0]
                    status_obj = status_map.get(chosen_status_name, all_statuses[0])

                    emp_id, dept_id, loc_id = None, None, None

                    if chosen_status_name == "В эксплуатации":
                        if all_emps: emp_id = random.choice(all_emps).id
                        if all_depts: dept_id = random.choice(all_depts).id
                        if all_locs: loc_id = random.choice(all_locs).id
                    elif chosen_status_name == "На складе":
                        if all_locs: loc_id = random.choice(all_locs).id

                    final_name = f"{scenario['brand_hint']} {scenario['model_name']}"
                    notes = scenario.get('notes_prefix', '') + " " + faker.sentence(nb_words=5)

                    asset_data = {
                        "name": final_name,
                        "inventory_number": f"INV-{purchase_date.year}-{faker.unique.random_number(digits=5)}",
                        "serial_number": faker.bothify(text='??-#######').upper(),
                        "mac_address": faker.mac_address() if target_type.name in ["ПК", "Ноутбук", "Сервер", "Сетевое оборудование"] else None,
                        "ip_address": faker.ipv4() if target_type.name in ["Сервер", "Сетевое оборудование", "Принтер"] else None,
                        "notes": notes.strip(),
                        "source": "Initial Seed (Scenario)",
                        "manufacturer_id": model.manufacturer_id,
                        "purchase_date": purchase_date,
                        "warranty_end_date": warranty_end,
                        "price": round(price, 2),
                        "expected_lifespan_years": scenario['lifespan'],
                        "current_wear_percentage": int(wear),
                        "asset_type_id": target_type.id,
                        "device_model_id": model.id,
                        "status_id": status_obj.id,
                        "department_id": dept_id,
                        "location_id": loc_id,
                        "employee_id": emp_id,
                        "tag_ids": []
                    }

                    await service.create_device(db, AssetCreate(**asset_data), user_id=ADMIN_USER_ID)
                    batch_created += 1
                    print('.', end='', flush=True)

                except Exception as e:
                    print(f'x ({e})', end='', flush=True)

            total_created += batch_created
            print(f" OK ({batch_created}/{scenario['count']})")

    print(f'\n\n✅ ВСЕГО СОЗДАНО: {total_created} активов.')
    print('Дашборд теперь отражает реальную структуру компании.')
    print('\n' + '=' * 50)
    print('🔐 ДАННЫЕ ДЛЯ ВХОДА:')
    print('   Email: admin@example.com')
    print('   Пароль: admin')
    print('=' * 50 + '\n')

if __name__ == '__main__':
    asyncio.run(seed_devices())
