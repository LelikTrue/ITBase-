# app/services/__init__.py

from .device_service import DeviceService
from .mixins.dependency_check_mixin import DependencyCheckMixin
from .mixins.duplicate_check_mixin import DuplicateCheckMixin

__all__ = ['DuplicateCheckMixin', 'DependencyCheckMixin']

device_service = DeviceService()
