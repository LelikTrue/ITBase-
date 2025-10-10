# app/api/endpoints/tags.py

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.tag import TagResponse
from app.services.tag_service import TagService

router = APIRouter()

# Провайдер для сервиса тегов
def get_tag_service() -> TagService:
    return TagService()

@router.get("/search", response_model=List[TagResponse])
async def search_tags_api(
    q: str = Query(..., min_length=1, description="Поисковый запрос для тегов"),
    db: AsyncSession = Depends(get_db),
    tag_service: TagService = Depends(get_tag_service)
):
    """
    API для поиска тегов. Используется для автодополнения в формах.
    """
    tags = await tag_service.search_tags(db, q)
    return tags