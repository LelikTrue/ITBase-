# app/services/__init__.py

from .device_service import DeviceService
from .mixins.duplicate_check_mixin import DuplicateCheckMixin
from .mixins.dependency_check_mixin import DependencyCheckMixin

__all__ = ["DuplicateCheckMixin", "DependencyCheckMixin"]

device_service = DeviceService()