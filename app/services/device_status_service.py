# app/services/device_status_service.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Device, DeviceStatus
from app.schemas.dictionary import DictionarySimpleCreate, DictionarySimpleUpdate
from app.services import DependencyCheckMixin, DuplicateCheckMixin
from app.services.base_service import BaseService


class DeviceStatusService(
    DuplicateCheckMixin,
    DependencyCheckMixin,
    BaseService[DeviceStatus, DictionarySimpleCreate, DictionarySimpleUpdate],
):
    """
    Сервис для управления статусами устройств.
    - Проверяет дубликаты по 'name'.
    - Проверяет связанные 'Device' перед удалением.
    """

    async def create(
        self, db: AsyncSession, obj_in: DictionarySimpleCreate, user_id: int
    ) -> DeviceStatus:
        await self._check_duplicate(db, "name", obj_in.name)
        return await super().create(db, obj_in, user_id)

    async def update(
        self,
        db: AsyncSession,
        obj_id: int,
        obj_in: DictionarySimpleUpdate,
        user_id: int,
    ) -> DeviceStatus | None:
        if obj_in.name:
            await self._check_duplicate(db, "name", obj_in.name, current_id=obj_id)
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(
        self, db: AsyncSession, obj_id: int, user_id: int
    ) -> DeviceStatus | None:
        await self._check_dependencies(db, Device.status_id, obj_id, "активов")
        return await super().delete(db, obj_id, user_id)


# Создаем единственный экземпляр сервиса, передавая ему модель
device_status_service = DeviceStatusService(DeviceStatus)
