# app/services/tag_service.py

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Tag
from app.schemas.tag import TagCreate, TagUpdate
from app.services.base_dictionary_service import BaseDictionaryService
from app.services.exceptions import DeletionError, DuplicateError


class TagService(BaseDictionaryService[Tag, TagCreate, TagUpdate]):
    def __init__(self):
        super().__init__(Tag, entity_name_russian='Тег')

    async def create(self, db: AsyncSession, data: TagCreate, user_id: int) -> Tag:
        """Создает новый тег."""
        try:
            new_item = Tag(**data.model_dump())
            db.add(new_item)
            await db.commit()
            await db.refresh(new_item)
            return new_item
        except IntegrityError:
            await db.rollback()
            raise DuplicateError(f"Тег с названием '{data.name}' уже существует.")

    async def update(self, db: AsyncSession, item_id: int, data: TagUpdate, user_id: int) -> Tag | None:
        """Обновляет тег."""
        db_item = await db.get(Tag, item_id)
        if not db_item:
            return None
        try:
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_item, key, value)
            await db.commit()
            await db.refresh(db_item)
            return db_item
        except IntegrityError:
            await db.rollback()
            raise DuplicateError(f"Тег с названием '{data.name}' уже существует.")

    async def delete(self, db: AsyncSession, item_id: int, user_id: int) -> Tag | None:
        """Удаляет тег."""
        # Для проверки зависимостей нам нужно загрузить связанные 'devices'
        db_item = await db.get(Tag, item_id, options=[selectinload(Tag.devices)])
        if not db_item:
            return None

        # Проверка на использование в устройствах через связь
        if db_item.devices:
            raise DeletionError(f"Нельзя удалить тег '{db_item.name}', так как он используется в {len(db_item.devices)} устройствах.")

        await db.delete(db_item)
        await db.commit()
        return db_item

    async def search_tags(self, db: AsyncSession, query: str) -> list[Tag]:
        """Ищет теги по имени."""
        if not query:
            return []

        search_query = f'%{query}%'
        stmt = select(Tag).where(Tag.name.ilike(search_query)).order_by(Tag.name).limit(20)
        result = await db.execute(stmt)
        return result.scalars().all()
