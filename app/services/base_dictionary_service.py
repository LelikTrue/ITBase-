# app/services/base_dictionary_service.py

from typing import Generic, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseDictionaryService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Базовый сервис для справочников.
    Предоставляет общую логику получения всех записей.
    """
    def __init__(self, model: Type[ModelType], entity_name_russian: str): # <--- ИЗМЕНИТЬ
        self.model = model
        self.entity_name_russian = entity_name_russian
        # Используется для логирования, чтобы соответствовать именам в таблице логов
        self.entity_name_for_log = self.model.__tablename__.replace('s', '_singular')

    async def get_all(self, db: AsyncSession) -> list[ModelType]:
        """Возвращает все записи справочника, отсортированные по имени."""
        # У большинства справочников есть поле 'name', сортируем по нему.
        order_attribute = getattr(self.model, 'name', self.model.id)
        stmt = select(self.model).order_by(order_attribute)
        result = await db.execute(stmt)
        return result.scalars().all()

    # Методы create, update, delete теперь не реализуются в базовом классе,
    # так как их логика (проверки, логирование) слишком специфична для каждой сущности.
    # Дочерние классы должны будут реализовать их самостоятельно.