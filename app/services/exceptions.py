# app/services/exceptions.py

class BaseServiceException(Exception):
    """Базовый класс для исключений сервисного слоя."""
    pass

class DuplicateError(BaseServiceException):
    """Исключение для дублирующихся записей (нарушение UNIQUE)."""
    pass

class DeletionError(BaseServiceException):
    """Исключение при невозможности удаления из-за зависимостей."""
    pass

class NotFoundError(BaseServiceException):
    """Исключение: запрашиваемая сущность не найдена (общая ошибка)."""
    pass

class DeviceNotFoundException(BaseServiceException):
    """Исключение: устройство не найдено."""
    pass

class DuplicateDeviceError(BaseServiceException):
    """Исключение: устройство с таким уникальным полем уже существует."""
    pass