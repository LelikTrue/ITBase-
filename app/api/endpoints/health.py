from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from app.db.database import get_db

router = APIRouter()


# Этот эндпоинт оставляем как есть, он для примера.
@router.get("/health", tags=["health"])
async def health_check():
    """Простая проверка, что API жив."""
    return {"status": "ok"}


# ИЗМЕНЯЕМ ЭТОТ ЭНДПОИНТ
@router.get("/ready", response_model=Dict[str, str], tags=["health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Проверяет готовность сервиса к приему трафика,
    включая подключение к базе данных.
    """
    try:
        # Выполняем простой запрос, чтобы убедиться, что соединение работает
        await db.execute(text("SELECT 1"))
        db_status = "ok"
        status_code = 200
    except Exception:
        db_status = "error"
        status_code = 503  # Service Unavailable

    response_data = {"db_status": db_status}

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=response_data)
    
    return response_data


# Этот эндпоинт можно удалить или оставить, он в тестах не участвует
@router.get("/startup", tags=["health"])
async def startup_check():
    """
    Проверка успешного запуска сервиса.
    """
    return {"status": "started"}
