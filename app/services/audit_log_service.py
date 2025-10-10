from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionLog

async def log_action(
    db: AsyncSession,
    user_id: int,
    action_type: str,
    entity_type: str,
    entity_id: int,
    details: Optional[Dict[str, Any]] = None
) -> ActionLog:
    """
    Асинхронно создает запись в логе действий
    
    Args:
        db: Сессия базы данных
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
    
    db.add(log_entry)
    # Убираем commit. Управление транзакцией теперь на стороне вызывающего кода.
    # Это позволяет объединять несколько операций в одну атомарную транзакцию.
    
    return log_entry
