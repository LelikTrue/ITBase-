# app/services/tag_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Tag
from app.schemas.tag import TagCreate, TagUpdate
from app.services.base_service import BaseService
from app.services.exceptions import DeletionError

class TagService(BaseService[Tag, TagCreate, TagUpdate]):
    async def create(self, db: AsyncSession, obj_in: TagCreate, user_id: int) -> Tag:
        await self._check_duplicate(db, "name", obj_in.name)
        return await super().create(db, obj_in, user_id)

    async def update(self, db: AsyncSession, obj_id: int, obj_in: TagUpdate, user_id: int) -> Tag | None:
        await self._check_duplicate(db, "name", obj_in.name, current_id=obj_id)
        return await super().update(db, obj_id, obj_in, user_id)

    async def delete(self, db: AsyncSession, obj_id: int, user_id: int) -> Tag | None:
        # Для M2M связи нужно подгрузить связанные объекты, чтобы проверить их наличие
        tag_to_delete = await db.get(Tag, obj_id, options=[selectinload(Tag.devices)])
        if tag_to_delete and tag_to_delete.devices:
            raise DeletionError(f"Невозможно удалить тег, так как он присвоен {len(tag_to_delete.devices)} активам.")
        
        # Если зависимостей нет, вызываем базовый метод удаления
        return await super().delete(db, obj_id, user_id)

tag_service = TagService(Tag)