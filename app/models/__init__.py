# Path: app/models/__init__.py

# Этот файл реэкспортирует все модели, делая их доступными для Alembic.
# Импортируем Base из центрального места, чтобы все модели могли его использовать.
from ..db.database import Base  # Alembic использует этот Base для автогенерации
from .action_log import ActionLog

# А теперь импортируем все конкретные модели
from .asset_type import AssetType
from .attachment import Attachment
from .base import BaseMixin
from .component import (
    Component,
    ComponentCPU,
    ComponentGPU,
    ComponentHistory,
    ComponentMotherboard,
    ComponentRAM,
    ComponentStorage,
)
from .department import Department
from .device import Device
from .device_model import DeviceModel
from .device_status import DeviceStatus
from .employee import Employee
from .location import Location
from .manufacturer import Manufacturer
from .network import NetworkSettings
from .supplier import Supplier
from .tag import Tag
from .user import User

__all__ = [
    'Base',
    'BaseMixin',
    'AssetType',
    'Department',
    'DeviceModel',
    'DeviceStatus',
    'Employee',
    'Location',
    'Manufacturer',
    'Attachment',
    'Device',
    'NetworkSettings',
    'ActionLog',
    'Tag',
    'Supplier',
    'Component',
    'ComponentCPU',
    'ComponentRAM',
    'ComponentStorage',
    'ComponentGPU',
    'ComponentMotherboard',
    'ComponentHistory',
]
