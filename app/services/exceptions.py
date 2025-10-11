# app/services/exceptions.py

class BaseServiceException(Exception):
    """Базовый класс для исключений сервисного слоя."""

class DuplicateError(BaseServiceException):
    """Исключение для дублирующихся записей (нарушение UNIQUE)."""

class DeletionError(BaseServiceException):
    """Исключение при невозможности удаления из-за зависимостей."""

class NotFoundError(BaseServiceException):
    """Исключение: запрашиваемая сущность не найдена (общая ошибка)."""

class DeviceNotFoundException(BaseServiceException):
    """Исключение: устройство не найдено."""

class DuplicateDeviceError(BaseServiceException):
    """Исключение: устройство с таким уникальным полем уже существует."""
