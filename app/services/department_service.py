from app.models import Department

from .base_dictionary_service import BaseDictionaryService


class DepartmentService(BaseDictionaryService):
    def __init__(self):
        super().__init__(
            model=Department,
            entity_name_russian='Отдел'
        )
