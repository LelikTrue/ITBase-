# app/services/base_service.py

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import Base
from app.services.audit_log_service import log_action
from app.services.exceptions import DuplicateError

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get_all(self, db: AsyncSession) -> list[ModelType]:
        stmt = select(self.model).order_by(self.model.id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, obj_id: int) -> ModelType | None:
        return await db.get(self.model, obj_id)

    async def create(
        self, db: AsyncSession, obj_in: CreateSchemaType, user_id: int
    ) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await log_action(
            db=db,
            user_id=user_id,
            action_type="create",
            entity_type=self.model.__name__,
            entity_id=db_obj.id,
            details=obj_in.model_dump(),
        )
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, obj_id: int, obj_in: UpdateSchemaType, user_id: int
    ) -> ModelType | None:
        db_obj = await self.get_by_id(db, obj_id)
        if not db_obj:
            return None

        old_data = {
            c.name: getattr(db_obj, c.name)
            for c in self.model.__table__.columns
            if hasattr(db_obj, c.name)
        }
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()

        diff = {
            k: {"old": old_data.get(k), "new": v}
            for k, v in update_data.items()
            if old_data.get(k) != v
        }
        if diff:
            await log_action(
                db=db,
                user_id=user_id,
                action_type="update",
                entity_type=self.model.__name__,
                entity_id=db_obj.id,
                details={"changes": diff},
            )

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self, db: AsyncSession, obj_id: int, user_id: int
    ) -> ModelType | None:
        db_obj = await self.get_by_id(db, obj_id)
        if not db_obj:
            return None

        obj_name = getattr(db_obj, "name", f"ID: {db_obj.id}")

        await log_action(
            db=db,
            user_id=user_id,
            action_type="delete",
            entity_type=self.model.__name__,
            entity_id=obj_id,
            details={"name": obj_name},
        )
        await db.delete(db_obj)
        await db.commit()
        return db_obj

    async def _check_duplicate(
        self,
        db: AsyncSession,
        field_name: str,
        value: Any,
        current_id: int | None = None,
    ):
        query = select(self.model.id).where(getattr(self.model, field_name) == value)
        if current_id:
            query = query.where(self.model.id != current_id)

        result = await db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            raise DuplicateError(
                f"Запись в '{self.model.__name__}' с таким '{field_name}' уже существует."
            )

    async def _count_related(
        self, db: AsyncSession, related_field: Any, obj_id: int
    ) -> int:
        # Примечание: obj_id=None не будет работать с `==`, поэтому для подсчета всех записей нужен отдельный метод
        if obj_id is None:
            query = select(func.count(self.model.id))
        else:
            query = select(func.count()).where(related_field == obj_id)
        result = await db.execute(query)
        return result.scalar_one()

    # --- ВОТ НОВЫЙ МЕТОД ---
    async def get_count(self, db: AsyncSession) -> int:
        """Возвращает общее количество записей для модели."""
        query = select(func.count(self.model.id))
        result = await db.execute(query)
        return result.scalar_one() or 0
