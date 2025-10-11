
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db

router = APIRouter()


# Этот эндпоинт оставляем как есть, он для примера.
@router.get('/health', tags=['health'])
async def health_check() -> dict[str, str]:
    """Простая проверка, что API жив."""
    return {'status': 'ok'}


# ИЗМЕНЯЕМ ЭТОТ ЭНДПОИНТ
@router.get('/ready', response_model=dict[str, str], tags=['health'])
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        # Выполняем простой запрос, чтобы убедиться, что соединение работает
        await db.execute(text('SELECT 1'))
        db_status = 'ok'
        status_code = 200
    except Exception:
        db_status = 'error'
        status_code = 503  # Service Unavailable

    response_data = {'db_status': db_status}

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=response_data)

    return response_data


# Этот эндпоинт можно удалить или оставить, он в тестах не участвует
@router.get('/startup', tags=['health'])
async def startup_check() -> dict[str, str]:
    """
    Проверка успешного запуска сервиса.
    """
    return {'status': 'started'}
