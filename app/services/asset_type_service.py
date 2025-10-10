from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, or_
from typing import Optional

from app.models import AssetType, Device
from app.schemas.dictionary import AssetTypeCreate, AssetTypeUpdate
from app.services.audit_log_service import log_action
from .base_dictionary_service import BaseDictionaryService
from .exceptions import DuplicateError, DeletionError

class AssetTypeService(BaseDictionaryService):
    """
    Сервис для управления типами активов.
    Наследует базовую логику, но переопределяет методы
    для обработки уникального поля 'prefix' и кастомной логики удаления.
    """
    def __init__(self):
        super().__init__(
            model=AssetType, 
            entity_name_russian="Тип актива"
        )

    # Метод get_all() теперь наследуется от BaseDictionaryService и его здесь нет.

    async def _check_duplicates(self, db: AsyncSession, name: str, prefix: str, item_id: Optional[int] = None):
        """Проверяет дубликаты по имени ИЛИ префиксу."""
        stmt = select(AssetType).where(
            or_(AssetType.name == name, AssetType.prefix == prefix)
        )
        if item_id:
            stmt = stmt.where(AssetType.id != item_id)
        
        result = await db.execute(stmt)
        existing_item = result.scalars().first()

        if existing_item:
            if existing_item.name == name:
                raise DuplicateError(f"Тип актива с названием '{name}' уже существует.")
            if existing_item.prefix == prefix:
                raise DuplicateError(f"Тип актива с префиксом '{prefix}' уже существует.")

    async def create(self, db: AsyncSession, data: AssetTypeCreate, user_id: int) -> AssetType:
        """Создает новый тип актива с проверкой на дубликаты имени и префикса."""
        name = data.name.strip()
        prefix = data.prefix.strip().upper()
        await self._check_duplicates(db, name, prefix)

        try:
            new_item = AssetType(
                name=name,
                prefix=prefix,
                description=data.description.strip() if data.description else None
            )
            db.add(new_item)
            await db.flush()

            await log_action(
                db=db, user_id=user_id, action_type="create",
                entity_type=self.entity_name_for_log, entity_id=new_item.id,
                details={"name": new_item.name, "prefix": new_item.prefix}
            )
            
            await db.commit()
            await db.refresh(new_item)
            return new_item
        except Exception:
            await db.rollback()
            raise

    async def update(self, db: AsyncSession, item_id: int, data: AssetTypeUpdate, user_id: int) -> Optional[AssetType]:
        """Обновляет тип актива с проверкой на дубликаты."""
        name = data.name.strip()
        prefix = data.prefix.strip().upper()
        await self._check_duplicates(db, name, prefix, item_id)

        db_item = await db.get(AssetType, item_id)
        if not db_item:
            return None

        try:
            old_values = {"name": db_item.name, "prefix": db_item.prefix, "description": db_item.description}
            
            db_item.name = name
            db_item.prefix = prefix
            db_item.description = data.description.strip() if data.description else None
            
            new_values = {"name": db_item.name, "prefix": db_item.prefix, "description": db_item.description}

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

    async def delete(self, db: AsyncSession, item_id: int, user_id: int) -> Optional[AssetType]:
        """Удаляет тип актива, проверяя зависимости в таблице Device."""
        db_item = await db.get(AssetType, item_id)
        if not db_item:
            return None

        devices_count_stmt = select(func.count(Device.id)).where(Device.asset_type_id == item_id)
        devices_count = await db.scalar(devices_count_stmt)
        
        if devices_count > 0:
            raise DeletionError(f"Нельзя удалить тип актива '{db_item.name}', так как он используется в {devices_count} устройствах.")

        try:
            item_name = db_item.name
            await db.delete(db_item)
            
            await log_action(
                db=db, user_id=user_id, action_type="delete",
                entity_type=self.entity_name_for_log, entity_id=item_id,
                details={"name": item_name}
            )
            await db.commit()
            return db_item
        except IntegrityError:
            await db.rollback()
            raise DeletionError(f"Невозможно удалить тип актива '{db_item.name}', так как он используется в других записях.")
        except Exception:
            await db.rollback()
            raise