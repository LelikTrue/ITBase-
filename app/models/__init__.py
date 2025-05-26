# app/models/__init__.py
# Этот файл реэкспортирует все модели из других файлов в этом пакете,
# делая их доступными при импорте "app.models".

# Импортируем все модели из asset.py
from .asset import (
    Device,
    AssetType,
    DeviceStatus,
    DeviceModel,
    Department,
    Employee,
    Location,
    Manufacturer,
    Attachment, # Если Attachment и ActionLog определены в asset.py
    ActionLog,  # добавьте их здесь
)

# Если у вас есть другие файлы с моделями в папке app/models/,
# например, app/models/user.py, то нужно импортировать их здесь:
# from .user import User
# from .audit_log import AuditLog # Если есть audit_log.py