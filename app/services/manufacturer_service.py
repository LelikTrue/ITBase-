# app/services/manufacturer_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DeviceModel, Manufacturer
from app.schemas.dictionary import DictionarySimpleCreate, DictionarySimpleUpdate
from app.services import DependencyCheckMixin, DuplicateCheckMixin
from app.services.base_service import BaseService


class ManufacturerService(
    DuplicateCheckMixin,
    DependencyCheckMixin,
    BaseService[Manufacturer, DictionarySimpleCreate, DictionarySimpleUpdate],
):
    """
    Сервис для управления производителями.
    - Проверяет дубликаты по 'name'.
    - Проверяет связанные 'DeviceModel' перед удалением.
    """

    async def create(
        self, db: AsyncSession, obj_in: DictionarySimpleCreate, user_id: int
    ) -> Manufacturer:
        # Уникальная логика: проверка дубликата по имени
        await self._check_duplicate(db, "name", obj_in.name)
        # Вызов базового метода
        return await super().create(db, obj_in, user_id)

    async def update(
        self,
        db: AsyncSession,
        obj_id: int,
        obj_in: DictionarySimpleUpdate,
        user_id: int,
    ) -> Manufacturer | None:
        # Уникальная логика: проверка дубликата по имени
        if obj_in.name:
            await self._check_duplicate(db, "name", obj_in.name, current_id=obj_id)
        # Вызов базового метода
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(
        self, db: AsyncSession, obj_id: int, user_id: int
    ) -> Manufacturer | None:
        # Уникальная логика: проверка зависимостей в DeviceModel
        await self._check_dependencies(
            db, DeviceModel.manufacturer_id, obj_id, "моделей устройств"
        )
        # Вызов базового метода
        return await super().delete(db, obj_id, user_id)


# Создаем единственный экземпляр сервиса, передавая ему модель
manufacturer_service = ManufacturerService(Manufacturer)
