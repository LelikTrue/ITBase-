# app/api/endpoints/health.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.database import AsyncSessionFactory

router = APIRouter()


# Простая проверка (не трогаем)
@router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Простая проверка, что API жив."""
    return {"status": "ok"}


# ИСПРАВЛЕННЫЙ /ready — без Depends(get_db)
@router.get("/ready", response_model=dict[str, str], tags=["health"])
async def readiness_check() -> dict[str, str]:
    """Проверка подключения к БД."""
    try:
        async with AsyncSessionFactory() as db:
            await db.execute(text("SELECT 1"))
        return {"db_status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail={"db_status": "error", "error": str(e)}
        )


# Можно оставить
@router.get("/startup", tags=["health"])
async def startup_check() -> dict[str, str]:
    return {"status": "started"}
