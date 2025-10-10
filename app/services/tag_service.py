# app/services/tag_service.py

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Tag

class TagService:
    """Сервис для бизнес-логики, связанной с тегами."""

    async def search_tags(self, db: AsyncSession, query: str) -> List[Tag]:
        """
        Ищет теги, имя которых содержит указанную подстроку (без учета регистра).
        """
        if not query:
            return []
            
        search_query = f"%{query}%"
        stmt = select(Tag).where(Tag.name.ilike(search_query)).order_by(Tag.name).limit(20)
        
        result = await db.execute(stmt)
        return result.scalars().all()