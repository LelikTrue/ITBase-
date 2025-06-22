# app/models/__init__.py
# Этот файл реэкспортирует все модели из других файлов в этом пакете,
# делая их доступными при импорте "app.models".

from .base import Base, BaseMixin
from .asset_type import AssetType
from .department import Department
from .device_model import DeviceModel
from .device_status import DeviceStatus
from .employee import Employee
from .location import Location
from .manufacturer import Manufacturer
from .attachment import Attachment
from .device import Device
from .action_log import ActionLog

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
    "ActionLog",
]