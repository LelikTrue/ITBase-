#!/usr/bin/env python3
"""
Скрипт для инициализации и заполнения базы данных начальными данными.

Использование:
  python init_data.py [команды]

Команды:
  --clean           : Очистить таблицы перед заполнением. ВНИМАНИЕ: все данные будут удалены!
  --models [м1 м2]  : Заполнить только указанные модели (например, departments manufacturers).
                      По умолчанию заполняются все.
"""
import sys
import json
import argparse
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.database import SessionLocal, engine
from app.models import (
    AssetType, DeviceModel, DeviceStatus, Manufacturer,
    Department, Location, Employee, Base
)

DATA_DIR = project_root / "initdb"

ICONS = {"ok": "✅", "warn": "⚠️", "run": "🚀", "clean": "🧹", "info": "ℹ️"}

def populate_model(db: Session, model_class, data: list, unique_field: str):
    """Универсальная функция для заполнения модели данными."""
    count = 0
    for item_data in data:
        # Проверяем существование по уникальному полю
        unique_value = item_data.get(unique_field)
        if not unique_value:
            continue
        existing = db.query(model_class).filter(getattr(model_class, unique_field) == unique_value).first()
        if not existing:
            db.add(model_class(**item_data))
            count += 1
    db.commit()
    print(f"  {ICONS['ok']} {model_class.__name__}: добавлено {count} новых записей.")

def init_device_models(db: Session):
    """Инициализация моделей устройств"""
    print(f"{ICONS['info']} Заполнение DeviceModel (со связями)...")
    filepath = DATA_DIR / "device_models.json"
    if not filepath.exists():
        print(f"  {ICONS['warn']} Файл {filepath.name} не найден, пропуск.")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Кэшируем связанные объекты для уменьшения запросов к БД
    manufacturers = {m.name: m.id for m in db.query(Manufacturer).all()}
    asset_types = {t.name: t.id for t in db.query(AssetType).all()}
    count = 0

    for item_data in data:
        # Проверяем существование
        existing = db.query(DeviceModel).filter(
            DeviceModel.name == item_data["name"],
            DeviceModel.manufacturer_id == manufacturers.get(item_data["manufacturer_name"])
        ).first()

        if not existing:
            # Заменяем имена на ID
            item_data["manufacturer_id"] = manufacturers.get(item_data.pop("manufacturer_name"))
            item_data["asset_type_id"] = asset_types.get(item_data.pop("asset_type_name"))

            if item_data["manufacturer_id"] and item_data["asset_type_id"]:
                db.add(DeviceModel(**item_data))
                count += 1

    db.commit()
    print(f"  {ICONS['ok']} DeviceModel: добавлено {count} новых записей.")

def clean_tables(db: Session, tables_to_clean: list):
    """Очищает указанные таблицы."""
    print(f"{ICONS['clean']} Очистка таблиц: {', '.join(tables_to_clean)}...")
    # Выключаем внешние ключи для TRUNCATE
    db.execute(text(f"TRUNCATE TABLE {', '.join(tables_to_clean)} RESTART IDENTITY CASCADE;"))
    db.commit()
    print(f"{ICONS['ok']} Таблицы успешно очищены.")

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Скрипт инициализации БД.")
    parser.add_argument(
        "--clean", action="store_true", help="Очистить таблицы перед заполнением."
    )
    parser.add_argument(
        "--models", nargs="+", help="Список моделей для заполнения (по умолчанию все)."
    )
    args = parser.parse_args()

    # Определяем порядок и метаданные для заполнения
    models_to_populate = {
        "asset_types": (AssetType, "name"),
        "manufacturers": (Manufacturer, "name"),
        "device_statuses": (DeviceStatus, "name"),
        "departments": (Department, "name"),
        "locations": (Location, "name"),
        "employees": (Employee, "employee_id"),
    }

    print(f"{ICONS['run']} Инициализация базы данных...")
    print("=" * 50)

    print(f"{ICONS['info']} Создание таблиц (если не существуют)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if args.clean:
            # Очищаем в обратном порядке зависимостей
            tables_to_clean = [
                "device_models", "employees", "locations", "departments",
                "device_statuses", "manufacturers", "asset_types"
            ]
            clean_tables(db, tables_to_clean)

        # Определяем, какие модели обрабатывать
        process_list = args.models if args.models else models_to_populate.keys()

        for model_name in process_list:
            if model_name in models_to_populate:
                model_class, unique_field = models_to_populate[model_name]
                filepath = DATA_DIR / f"{model_name}.json"
                if filepath.exists():
                    print(f"{ICONS['info']} Заполнение {model_class.__name__}...")
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    populate_model(db, model_class, data, unique_field)
                else:
                    print(f"  {ICONS['warn']} Файл {filepath.name} не найден, пропуск.")

        # Обрабатываем DeviceModel отдельно из-за зависимостей
        if not args.models or "device_models" in args.models:
            init_device_models(db)

        print("=" * 50)
        print(f"{ICONS['ok']} Инициализация завершена успешно!")

    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        db.rollback()
        return 1
    finally:
        db.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())