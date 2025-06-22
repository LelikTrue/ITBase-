from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession # Импортируем AsyncSession

from app.models import ActionLog

async def log_action( # Функция стала асинхронной
    db: Session,
    user_id: int,
    action_type: str,
    entity_type: str,
    entity_id: int,
    details: Optional[Dict[str, Any]] = None
) -> ActionLog:
    """
    Создает запись в логе действий
    
    Args:
        db: Асинхронная сессия базы данных
        user_id: ID пользователя, выполнившего действие
        action_type: Тип действия (create, update, delete, etc.)
        entity_type: Тип сущности (Device, Employee, etc.)
        entity_id: ID сущности
        details: Дополнительные детали действия
        
    Returns:
        ActionLog: Созданная запись лога
    """
    log_entry = ActionLog(
        user_id=user_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {}
    )
    
    db.add(log_entry) # add is synchronous
    await db.commit()
    await db.refresh(log_entry)
    
    return log_entry
