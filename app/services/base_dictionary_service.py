
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base
from app.schemas.dictionary import DictionarySimpleCreate, DictionarySimpleUpdate
from app.services.audit_log_service import log_action

from .exceptions import DeletionError, DuplicateError


class BaseDictionaryService:
    """
    Универсальный базовый сервис для простых справочников 
    (Location, Department, Manufacturer, DeviceStatus).
    """
    def __init__(self, model: type[Base], entity_name_russian: str):
        """
        Инициализирует сервис.
        :param model: Класс модели SQLAlchemy (например, Location).
        :param entity_name_russian: Название сущности на русском в именительном падеже 
                                    (например, "Местоположение").
        """
        self.model = model
        self.entity_name_for_log = model.__name__
        self.entity_name_russian = entity_name_russian.capitalize()

    async def _check_duplicate(self, db: AsyncSession, name: str, item_id: int | None = None):
        """Проверяет, существует ли запись с таким же именем."""
        stmt = select(self.model).where(self.model.name == name)
        if item_id:
            stmt = stmt.where(self.model.id != item_id)

        result = await db.execute(stmt)
        if result.scalars().first():
            raise DuplicateError(f"{self.entity_name_russian} с названием '{name}' уже существует.")

    async def get_all(self, db: AsyncSession) -> list[Base]:
        stmt = select(self.model).order_by(self.model.name)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, data: DictionarySimpleCreate, user_id: int) -> Base:
        """Создает новую запись с предварительной проверкой на дубликат."""
        await self._check_duplicate(db, data.name)

        try:
            new_item = self.model(
                name=data.name.strip(),
                description=data.description.strip() if data.description else None
            )
            db.add(new_item)
            await db.flush()

            await log_action(
                db=db, user_id=user_id, action_type='create',
                entity_type=self.entity_name_for_log, entity_id=new_item.id,
                details={'name': new_item.name}
            )

            await db.commit()
            await db.refresh(new_item)
            return new_item
        except Exception:
            await db.rollback()
            raise

    async def update(self, db: AsyncSession, item_id: int, data: DictionarySimpleUpdate, user_id: int) -> Base | None:
        """Обновляет существующую запись."""
        await self._check_duplicate(db, data.name, item_id)

        db_item = await db.get(self.model, item_id)
        if not db_item:
            return None

        try:
            old_values = {'name': db_item.name, 'description': db_item.description}

            db_item.name = data.name.strip()
            db_item.description = data.description.strip() if data.description else None

            new_values = {'name': db_item.name, 'description': db_item.description}

            await log_action(
                db=db, user_id=user_id, action_type='update',
                entity_type=self.entity_name_for_log, entity_id=db_item.id,
                details={'old': old_values, 'new': new_values}
            )
            await db.commit()
            await db.refresh(db_item)
            return db_item
        except Exception:
            await db.rollback()
            raise

    async def delete(self, db: AsyncSession, item_id: int, user_id: int) -> Base | None:
        """Удаляет запись."""
        db_item = await db.get(self.model, item_id)
        if not db_item:
            return None

        try:
            item_name = db_item.name
            await db.delete(db_item)

            await log_action(
                db=db, user_id=user_id, action_type='delete',
                entity_type=self.entity_name_for_log, entity_id=item_id,
                details={'name': item_name}
            )
            await db.commit()
            return db_item
        except IntegrityError:
            await db.rollback()
            raise DeletionError(f"Невозможно удалить '{item_name}', так как эта запись используется.")
        except Exception:
            await db.rollback()
            raise
