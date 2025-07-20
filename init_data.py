#!/usr/bin/env python3
"""
Скрипт для заполнения базы данных начальными данными
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.models import (
    AssetType, DeviceModel, DeviceStatus, Manufacturer, 
    Department, Location, Employee, Base
)

def create_tables():
    """Создает все таблицы в базе данных"""
    print("🔧 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")

def init_asset_types(db: Session):
    """Инициализация типов активов"""
    print("📦 Добавление типов активов...")
    
    asset_types = [
        {"name": "Компьютер", "description": "Настольные и портативные ком��ьютеры"},
        {"name": "Монитор", "description": "Мониторы и дисплеи"},
        {"name": "Принтер", "description": "Принтеры и МФУ"},
        {"name": "Сетевое оборудование", "description": "Роутеры, коммутаторы, точки доступа"},
        {"name": "Сервер", "description": "Серверное оборудование"},
        {"name": "Мобильное устройство", "description": "Телефоны, планшеты"},
        {"name": "Периферия", "description": "Клавиатуры, мыши, веб-камеры"},
        {"name": "Аудио/Видео", "description": "Колонки, наушники, проекторы"},
    ]
    
    for asset_type_data in asset_types:
        existing = db.query(AssetType).filter(AssetType.name == asset_type_data["name"]).first()
        if not existing:
            asset_type = AssetType(**asset_type_data)
            db.add(asset_type)
    
    db.commit()
    print(f"✅ Добавлено {len(asset_types)} типов активов")

def init_manufacturers(db: Session):
    """Инициализация производителей"""
    print("🏭 Добавление производителей...")
    
    manufacturers = [
        {"name": "Dell", "description": "Dell Technologies"},
        {"name": "HP", "description": "Hewlett-Packard"},
        {"name": "Lenovo", "description": "Lenovo Group"},
        {"name": "ASUS", "description": "ASUSTeK Computer"},
        {"name": "Acer", "description": "Acer Inc."},
        {"name": "Apple", "description": "Apple Inc."},
        {"name": "Samsung", "description": "Samsung Electronics"},
        {"name": "LG", "description": "LG Electronics"},
        {"name": "Canon", "description": "Canon Inc."},
        {"name": "Epson", "description": "Seiko Epson"},
        {"name": "Cisco", "description": "Cisco Systems"},
        {"name": "D-Link", "description": "D-Link Corporation"},
        {"name": "TP-Link", "description": "TP-Link Technologies"},
        {"name": "Logitech", "description": "Logitech International"},
        {"name": "Microsoft", "description": "Microsoft Corporation"},
    ]
    
    for manufacturer_data in manufacturers:
        existing = db.query(Manufacturer).filter(Manufacturer.name == manufacturer_data["name"]).first()
        if not existing:
            manufacturer = Manufacturer(**manufacturer_data)
            db.add(manufacturer)
    
    db.commit()
    print(f"✅ Добавлено {len(manufacturers)} производителей")

def init_device_statuses(db: Session):
    """Инициализация статусов устройств"""
    print("📊 Добавление статусов устройств...")
    
    statuses = [
        {"name": "Активен", "description": "Устройство используется"},
        {"name": "В резерве", "description": "Устройство готово к использованию"},
        {"name": "На ремонте", "description": "Устройство находится в ремонте"},
        {"name": "Списан", "description": "Устройство списано"},
        {"name": "Утерян", "description": "Устройство утеряно"},
        {"name": "Украден", "description": "Устройство украдено"},
        {"name": "На складе", "description": "Устройство на складе"},
        {"name": "Передан", "description": "Устройство передано другой организации"},
    ]
    
    for status_data in statuses:
        existing = db.query(DeviceStatus).filter(DeviceStatus.name == status_data["name"]).first()
        if not existing:
            status = DeviceStatus(**status_data)
            db.add(status)
    
    db.commit()
    print(f"✅ Добавлено {len(statuses)} статусов устройств")

def init_departments(db: Session):
    """Инициализация отделов"""
    print("🏢 Добавление отделов...")
    
    departments = [
        {"name": "ИТ отдел", "description": "Отдел информационных технологий"},
        {"name": "Бухгалтерия", "description": "Бухгалтерский отдел"},
        {"name": "Отдел кадров", "description": "Управление персоналом"},
        {"name": "Юридический отдел", "description": "Юридическая служба"},
        {"name": "Отдел продаж", "description": "Отдел продаж и маркетинга"},
        {"name": "Производство", "description": "Производственный отдел"},
        {"name": "Склад", "description": "Складское хозяйство"},
        {"name": "Администрация", "description": "Административный отдел"},
        {"name": "Безопасность", "description": "Служба безопасности"},
        {"name": "Техподдержка", "description": "Техническая поддержка"},
    ]
    
    for department_data in departments:
        existing = db.query(Department).filter(Department.name == department_data["name"]).first()
        if not existing:
            department = Department(**department_data)
            db.add(department)
    
    db.commit()
    print(f"✅ Добавлено {len(departments)} отделов")

def init_locations(db: Session):
    """Инициализация местоположений"""
    print("📍 Добавление местоположений...")
    
    locations = [
        {"name": "Офис 1 этаж", "description": "Первый этаж главного офиса"},
        {"name": "Офис 2 этаж", "description": "Второй этаж главного офиса"},
        {"name": "Офис 3 этаж", "description": "Третий этаж главного офиса"},
        {"name": "Серверная", "description": "Серверная комната"},
        {"name": "Склад", "description": "Основной склад"},
        {"name": "Переговорная 1", "description": "Переговорная комната №1"},
        {"name": "Переговорная 2", "description": "Переговорная комната №2"},
        {"name": "Конференц-зал", "description": "Большой конференц-зал"},
        {"name": "Приемная", "description": "Приемная директора"},
        {"name": "Удаленная работа", "description": "Сотрудник работает удаленно"},
    ]
    
    for location_data in locations:
        existing = db.query(Location).filter(Location.name == location_data["name"]).first()
        if not existing:
            location = Location(**location_data)
            db.add(location)
    
    db.commit()
    print(f"✅ Добавлено {len(locations)} местоположений")

def init_employees(db: Session):
    """Инициализация сотрудников"""
    print("👥 Добавление сотрудников...")
    
    employees = [
        {
            "first_name": "Иван",
            "last_name": "Иванов",
            "patronymic": "Иванович",
            "employee_id": "EMP001",
            "email": "i.ivanov@company.com",
            "phone_number": "+7 (999) 123-45-67"
        },
        {
            "first_name": "Петр",
            "last_name": "Петров",
            "patronymic": "Петрович",
            "employee_id": "EMP002",
            "email": "p.petrov@company.com",
            "phone_number": "+7 (999) 234-56-78"
        },
        {
            "first_name": "Анна",
            "last_name": "Сидорова",
            "patronymic": "Александровна",
            "employee_id": "EMP003",
            "email": "a.sidorova@company.com",
            "phone_number": "+7 (999) 345-67-89"
        },
        {
            "first_name": "Михаил",
            "last_name": "Козлов",
            "patronymic": "Сергеевич",
            "employee_id": "EMP004",
            "email": "m.kozlov@company.com",
            "phone_number": "+7 (999) 456-78-90"
        },
        {
            "first_name": "Елена",
            "last_name": "Смирнова",
            "patronymic": "Викторовна",
            "employee_id": "EMP005",
            "email": "e.smirnova@company.com",
            "phone_number": "+7 (999) 567-89-01"
        },
    ]
    
    for employee_data in employees:
        existing = db.query(Employee).filter(Employee.employee_id == employee_data["employee_id"]).first()
        if not existing:
            employee = Employee(**employee_data)
            db.add(employee)
    
    db.commit()
    print(f"✅ Добавлено {len(employees)} сотрудников")

def init_device_models(db: Session):
    """Инициализация моделей устройств"""
    print("💻 Добавление моделей устройств...")
    
    # Получаем ID типов активов и производителей
    computer_type = db.query(AssetType).filter(AssetType.name == "Компьютер").first()
    monitor_type = db.query(AssetType).filter(AssetType.name == "Монитор").first()
    printer_type = db.query(AssetType).filter(AssetType.name == "Принтер").first()
    
    dell = db.query(Manufacturer).filter(Manufacturer.name == "Dell").first()
    hp = db.query(Manufacturer).filter(Manufacturer.name == "HP").first()
    lenovo = db.query(Manufacturer).filter(Manufacturer.name == "Lenovo").first()
    
    if not all([computer_type, monitor_type, printer_type, dell, hp, lenovo]):
        print("⚠️ Не найдены необходимые типы активов или производители")
        return
    
    device_models = [
        {
            "name": "OptiPlex 7090",
            "manufacturer_id": dell.id,
            "asset_type_id": computer_type.id,
            "description": "Настольный компьютер Dell OptiPlex 7090",
            "specification": {"cpu": "Intel Core i5", "ram": "8GB", "storage": "256GB SSD"}
        },
        {
            "name": "ThinkPad T14",
            "manufacturer_id": lenovo.id,
            "asset_type_id": computer_type.id,
            "description": "Ноутбук Lenovo ThinkPad T14",
            "specification": {"cpu": "Intel Core i7", "ram": "16GB", "storage": "512GB SSD"}
        },
        {
            "name": "EliteBook 850",
            "manufacturer_id": hp.id,
            "asset_type_id": computer_type.id,
            "description": "Ноутбук HP EliteBook 850",
            "specification": {"cpu": "Intel Core i5", "ram": "8GB", "storage": "256GB SSD"}
        },
        {
            "name": "UltraSharp U2419H",
            "manufacturer_id": dell.id,
            "asset_type_id": monitor_type.id,
            "description": "Монитор Dell UltraSharp 24 дюйма",
            "specification": {"size": "24 inch", "resolution": "1920x1080", "type": "IPS"}
        },
        {
            "name": "LaserJet Pro M404n",
            "manufacturer_id": hp.id,
            "asset_type_id": printer_type.id,
            "description": "Лазерный принтер HP LaserJet Pro",
            "specification": {"type": "Laser", "color": "Monochrome", "speed": "38 ppm"}
        },
    ]
    
    for model_data in device_models:
        existing = db.query(DeviceModel).filter(
            DeviceModel.name == model_data["name"],
            DeviceModel.manufacturer_id == model_data["manufacturer_id"]
        ).first()
        if not existing:
            device_model = DeviceModel(**model_data)
            db.add(device_model)
    
    db.commit()
    print(f"✅ Добавлено {len(device_models)} моделей устройств")

def main():
    """Основная функция"""
    print("🚀 Инициализация базы данных начальными данными")
    print("=" * 50)
    
    try:
        # Создаем таблицы
        create_tables()
        
        # Создаем сессию
        db = SessionLocal()
        
        try:
            # Инициализируем справочники
            init_asset_types(db)
            init_manufacturers(db)
            init_device_statuses(db)
            init_departments(db)
            init_locations(db)
            init_employees(db)
            init_device_models(db)
            
            print("\n" + "=" * 50)
            print("🎉 Инициализация завершена успешно!")
            print("=" * 50)
            print("\n📋 Что добавлено:")
            print("   ✅ Типы активов (8 записей)")
            print("   ✅ Производители (15 записей)")
            print("   ✅ Статусы устройств (8 записей)")
            print("   ✅ Отделы (10 записей)")
            print("   ✅ Местоположения (10 записей)")
            print("   ✅ Сотрудники (5 записей)")
            print("   ✅ Модели устройств (5 записей)")
            print("\n🌐 Теперь вы можете:")
            print("   - Добавлять новые активы через веб-интерфейс")
            print("   - Использовать кнопки '+' для добавления новых справочников")
            print("   - Заполнять формы тестовыми данными")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())