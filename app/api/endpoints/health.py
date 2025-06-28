from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from app.db.session import get_db

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any], tags=["health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Проверка работоспособности сервиса.
    
    Проверяет:
    - Доступность API
    - Подключение к базе данных
    - Другие критические зависимости
    
    Returns:
        Dict: Статус сервиса и его компонентов
    """
    status = {
        "status": "ok",
        "version": "1.0.0",
        "services": {
            "database": "ok",
        }
    }
    
    # Проверка подключения к базе данных
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        status["status"] = "error"
        status["services"]["database"] = f"error: {str(e)}"
    
    # Если есть ошибки, возвращаем 503 Service Unavailable
    if status["status"] == "error":
        raise HTTPException(
            status_code=503,
            detail=status
        )
    
    return status


@router.get("/ready", tags=["health"])
async def readiness_check():
    """
    Проверка готовности сервиса к работе.
    
    Используется для проверки готовности сервиса к приему трафика.
    Kubernetes использует этот эндпоинт для проверки готовности пода.
    """
    return {"status": "ready"}


@router.get("/startup", tags=["health"])
async def startup_check():
    """
    Проверка успешного запуска сервиса.
    
    Используется для проверки успешного запуска сервиса.
    Kubernetes использует этот эндпоинт для проверки успешности старта пода.
    """
    return {"status": "started"}
