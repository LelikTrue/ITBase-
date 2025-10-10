from app.models import Location
from .base_dictionary_service import BaseDictionaryService

class LocationService(BaseDictionaryService):
    def __init__(self):
        super().__init__(
            model=Location, 
            entity_name_russian="Местоположение"
        )