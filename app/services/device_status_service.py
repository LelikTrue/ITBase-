from app.models import DeviceStatus
from .base_dictionary_service import BaseDictionaryService

class DeviceStatusService(BaseDictionaryService):
    def __init__(self):
        super().__init__(
            model=DeviceStatus, 
            entity_name_russian="Статус устройства"
        )