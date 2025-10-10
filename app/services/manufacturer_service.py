from app.models import Manufacturer
from .base_dictionary_service import BaseDictionaryService

class ManufacturerService(BaseDictionaryService):
    def __init__(self):
        super().__init__(
            model=Manufacturer, 
            entity_name_russian="Производитель"
        )