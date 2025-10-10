# Path: app/services/device_model_service.py

import logging
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Device, DeviceModel, Manufacturer, AssetType
from app.schemas.dictionary import DeviceModelCreate, DeviceModelUpdate
from app.services.audit_log_service import log_action
from .base_dictionary_service import BaseDictionaryService
from .exceptions import DeletionError, DuplicateError, NotFoundError

logger = logging.getLogger(__name__)

class DeviceModelService(BaseDictionaryService):
    """
    Сервис для бизнес-логики, связанной с моделями устройств.
    Наследует от BaseDictionaryService для единообразия, но переопределяет
    все ключевые методы для реализации специфичной бизнес-логики.
    """
    def __init__(self):
        # Мы все еще вызываем super().__init__, хотя почти все переопределяем.
        # Это хорошая практика для поддержания архитектурной целостности.
        super().__init__(
            model=DeviceModel,
            entity_name_russian="Модель устройства"
        )
    
    async def _check_related_entities_exist(self, db: AsyncSession, manufacturer_id: int, asset_type_id: int):
        """Проверяет, что производитель и тип актива существуют."""
        manufacturer = await db.get(Manufacturer, manufacturer_id)
        if not manufacturer:
            raise NotFoundError(f"Производитель с ID {manufacturer_id} не найден.")
        
        asset_type = await db.get(AssetType, asset_type_id)
        if not asset_type:
            raise NotFoundError(f"Тип актива с ID {asset_type_id} не найден.")
        
        return manufacturer, asset_type

    async def _check_duplicate(self, db: AsyncSession, name: str, manufacturer_id: int, item_id: Optional[int] = None):
        """Проверяет уникальность по паре (name, manufacturer_id)."""
        stmt = select(DeviceModel).where(
            DeviceModel.name == name,
            DeviceModel.manufacturer_id == manufacturer_id
        )
        if item_id:
            stmt = stmt.where(DeviceModel.id != item_id)
        
        result = await db.execute(stmt)
        if result.scalars().first():
            raise DuplicateError(f"Модель '{name}' для данного производителя уже существует.")

    async def get_all(self, db: AsyncSession):
        """Получает список всех моделей, подгружая связанные сущности."""
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.manufacturer), 
                selectinload(self.model.asset_type)
            )
            .order_by(self.model.name)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, item_id: int):
        """Получает одну модель устройства по ID с ее связями."""
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.manufacturer), 
                selectinload(self.model.asset_type)
            )
            .where(self.model.id == item_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, data: DeviceModelCreate, user_id: int) -> DeviceModel:
        """Создает новую модель устройства с предварительными проверками."""
        # Шаг 1: Проверка на дубликат.
        await self._check_duplicate(db, data.name, data.manufacturer_id)
        
        # Шаг 2: Проверка на существование связанных сущностей.
        manufacturer, asset_type = await self._check_related_entities_exist(db, data.manufacturer_id, data.asset_type_id)
        
        try:
            new_item = self.model(**data.model_dump())
            db.add(new_item)
            await db.flush()

            await log_action(
                db=db, user_id=user_id, action_type="create",
                entity_type=self.entity_name_for_log, entity_id=new_item.id,
                details={
                    "name": new_item.name,
                    "manufacturer": manufacturer.name,
                    "asset_type": asset_type.name,
                },
            )
            await db.commit()
            await db.refresh(new_item)
            return new_item
        except Exception:
            await db.rollback()
            raise

    async def update(self, db: AsyncSession, item_id: int, data: DeviceModelUpdate, user_id: int) -> Optional[DeviceModel]:
        """Обновляет модель устройства с предварительными проверками."""
        db_item = await self.get_by_id(db, item_id)
        if not db_item:
            return None

        # Шаг 1: Проверка на дубликат, если имя или производитель меняются.
        await self._check_duplicate(db, data.name, data.manufacturer_id, item_id)
        
        # Шаг 2: Проверка на существование связанных сущностей.
        await self._check_related_entities_exist(db, data.manufacturer_id, data.asset_type_id)

        try:
            old_values = {
                "name": db_item.name,
                "manufacturer_id": db_item.manufacturer_id,
                "asset_type_id": db_item.asset_type_id,
                "description": db_item.description
            }
            
            db_item.name = data.name
            db_item.manufacturer_id = data.manufacturer_id
            db_item.asset_type_id = data.asset_type_id
            db_item.description = data.description
            
            new_values = {
                "name": db_item.name,
                "manufacturer_id": db_item.manufacturer_id,
                "asset_type_id": db_item.asset_type_id,
                "description": db_item.description
            }

            await log_action(
                db=db, user_id=user_id, action_type="update",
                entity_type=self.entity_name_for_log, entity_id=db_item.id,
                details={"old": old_values, "new": new_values}
            )
            await db.commit()
            await db.refresh(db_item)
            return db_item
        except Exception:
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, item_id: int, user_id: int) -> Optional[DeviceModel]:
        """Удаляет модель, проверяя зависимости в таблице Device."""
        db_item = await db.get(self.model, item_id)
        if not db_item:
            return None

        devices_count = await db.scalar(
            select(func.count(Device.id)).where(Device.device_model_id == item_id)
        )
        if devices_count > 0:
            raise DeletionError(f"Нельзя удалить модель '{db_item.name}'. Используется в {devices_count} устройствах.")

        try:
            item_name = db_item.name
            await db.delete(db_item)
            await log_action(
                db=db, user_id=user_id, action_type="delete",
                entity_type=self.entity_name_for_log, entity_id=item_id,
                details={"name": item_name},
            )
            await db.commit()
            return db_item
        except Exception:
            await db.rollback()
            raise