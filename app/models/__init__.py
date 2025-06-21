# app/models/__init__.py
# Этот файл реэкспортирует все модели из других файлов в этом пакете,
# делая их доступными при импорте "app.models".

# Импортируем все модели из центрального файла asset.py
from .asset import (
    Device,
    Manufacturer,
    DeviceModel,
    Department,
    Location,
    Employee,
    AssetType,
    DeviceStatus,
    Attachment,
    ActionLog
)

# Также импортируем базовые классы для удобства
from .base import Base, BaseMixin