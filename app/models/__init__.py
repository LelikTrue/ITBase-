# Path: app/models/__init__.py

# Этот файл реэкспортирует все модели, делая их доступными для Alembic.

# Импортируем Base и BaseMixin из их правильных мест
from ..db.database import Base
from .base import BaseMixin

# А теперь импортируем все конкретные модели
from .asset_type import AssetType
from .department import Department
from .device_model import DeviceModel
from .device_status import DeviceStatus
from .employee import Employee
from .location import Location
from .manufacturer import Manufacturer
from .attachment import Attachment
from .device import Device
from .network import NetworkSettings
from .action_log import ActionLog
from .tag import Tag
from .supplier import Supplier

__all__ = [
    "Base",
    "BaseMixin",
    "AssetType",
    "Department",
    "DeviceModel",
    "DeviceStatus",
    "Employee",
    "Location",
    "Manufacturer",
    "Attachment",
    "Device",
    "NetworkSettings",
    "ActionLog",
    "Tag",
    "Supplier",  # <-- И ЭТА СТРОКА СЮДА
]