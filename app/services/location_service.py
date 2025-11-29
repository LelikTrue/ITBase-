# app/services/location_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, Location
from app.schemas.dictionary import DictionarySimpleCreate, DictionarySimpleUpdate
from app.services import DependencyCheckMixin, DuplicateCheckMixin
from app.services.base_service import BaseService


class LocationService(
    DuplicateCheckMixin,
    DependencyCheckMixin,
    BaseService[Location, DictionarySimpleCreate, DictionarySimpleUpdate],
):
    """
    Сервис для управления местоположениями.
    - Проверяет дубликаты по 'name'.
    - Проверяет связанные 'Device' перед удалением.
    """

    async def create(
        self, db: AsyncSession, obj_in: DictionarySimpleCreate, user_id: int
    ) -> Location:
        await self._check_duplicate(db, 'name', obj_in.name)
        return await super().create(db, obj_in, user_id)

    async def update(
        self,
        db: AsyncSession,
        obj_id: int,
        obj_in: DictionarySimpleUpdate,
        user_id: int,
    ) -> Location | None:
        if obj_in.name:
            await self._check_duplicate(db, 'name', obj_in.name, current_id=obj_id)
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(
        self, db: AsyncSession, obj_id: int, user_id: int
    ) -> Location | None:
        await self._check_dependencies(db, Device.location_id, obj_id, 'активов')
        return await super().delete(db, obj_id, user_id)


# Создаем единственный экземпляр сервиса, передавая ему модель
location_service = LocationService(Location)
