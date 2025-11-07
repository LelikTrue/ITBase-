# app/services/asset_type_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AssetType, Device, DeviceModel
from app.schemas.dictionary import AssetTypeCreate, AssetTypeUpdate
from app.services.base_service import BaseService
from app.services.exceptions import DeletionError

class AssetTypeService(BaseService[AssetType, AssetTypeCreate, AssetTypeUpdate]):
    """
    Сервис для управления типами активов.
    Использует BaseService, но переопределяет методы для добавления
    уникальной бизнес-логики:
    - Проверка на дубликаты по двум полям: 'name' и 'prefix'.
    - Проверка на связанные 'Device' и 'DeviceModel' перед удалением.
    """
    
    async def create(self, db: AsyncSession, obj_in: AssetTypeCreate, user_id: int) -> AssetType:
        # Уникальная логика: проверка дубликатов по двум полям
        await self._check_duplicate(db, "name", obj_in.name)
        await self._check_duplicate(db, "prefix", obj_in.prefix)
        # Вызов базового метода для создания, логирования и коммита
        return await super().create(db, obj_in, user_id)

    async def update(self, db: AsyncSession, obj_id: int, obj_in: AssetTypeUpdate, user_id: int) -> AssetType | None:
        # Уникальная логика: проверка дубликатов по двум полям с учетом ID текущего объекта
        if obj_in.name:
            await self._check_duplicate(db, "name", obj_in.name, current_id=obj_id)
        if obj_in.prefix:
            await self._check_duplicate(db, "prefix", obj_in.prefix, current_id=obj_id)
        # Вызов базового метода для обновления, логирования и коммита
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(self, db: AsyncSession, obj_id: int, user_id: int) -> AssetType | None:
        # Уникальная логика: проверка зависимостей в двух таблицах
        related_models_count = await self._count_related(db, DeviceModel.asset_type_id, obj_id)
        if related_models_count > 0:
            raise DeletionError(f"Невозможно удалить тип актива, так как с ним связано {related_models_count} моделей устройств.")
        
        related_devices_count = await self._count_related(db, Device.asset_type_id, obj_id)
        if related_devices_count > 0:
            raise DeletionError(f"Невозможно удалить тип актива, так как с ним связано {related_devices_count} активов.")
            
        # Если зависимостей нет, вызываем базовый метод для удаления
        return await super().delete(db, obj_id, user_id)

# Создаем единственный экземпляр сервиса, передавая ему модель, с которой он работает
asset_type_service = AssetTypeService(AssetType)