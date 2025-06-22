from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from sqlalchemy import select # Import select for async queries

from app.db.database import get_db
from app.models import ActionLog
from app.schemas.audit_log import ActionLog as ActionLogSchema
from app.templating import templates
import logging # Import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Audit Logs"])

@router.get("/audit-logs", name="view_audit_logs_page")
async def view_logs_page(
    request: Request,
    db: Session = Depends(get_db),
    action_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    entity_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    query = select(ActionLog) # Use select

    if user_id is not None:
        query = query.where(ActionLog.user_id == user_id)
    if action_type:
        query = query.where(ActionLog.action_type == action_type)
    if entity_type:
        query = query.where(ActionLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.where(ActionLog.entity_id == entity_id)
    if start_date:
        query = query.where(ActionLog.timestamp >= start_date)
    if end_date:
        # Прибавляем один день, чтобы включить все события за указанную дату
        query = query.where(ActionLog.timestamp < end_date + timedelta(days=1))

    logs_result = await db.execute(query.order_by(ActionLog.timestamp.desc()))
    logs = logs_result.scalars().all()

    # Получаем уникальные значения для фильтров
    action_types_result = await db.execute(select(ActionLog.action_type).distinct())
    action_types = action_types_result.all()
    entity_types_result = await db.execute(select(ActionLog.entity_type).distinct())
    entity_types = entity_types_result.all()

    context = {
        "request": request,
        "title": "Журнал действий",
        "logs": logs,
        "action_types": [item[0] for item in action_types if item[0]],
        "entity_types": [item[0] for item in entity_types if item[0]],
        "filters": {
            "action_type": action_type,
            "entity_type": entity_type,
            "user_id": user_id,
            "entity_id": entity_id,
            "start_date": start_date,
            "end_date": end_date,
        }
    }
    return templates.TemplateResponse("audit_logs.html", context)


@router.get("/api/logs", response_model=List[ActionLogSchema])
async def get_action_logs_api(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Получить логи действий с возможностью фильтрации
    """
    query = select(ActionLog) # Use select
    
    if user_id is not None:
        query = query.where(ActionLog.user_id == user_id)
    if action_type:
        query = query.where(ActionLog.action_type == action_type)
    if entity_type:
        query = query.where(ActionLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.where(ActionLog.entity_id == entity_id)
    if start_date:
        query = query.where(ActionLog.timestamp >= start_date)
    if end_date:
        query = query.where(ActionLog.timestamp <= end_date)
    
    logs_result = await db.execute(query.order_by(ActionLog.timestamp.desc()).offset(skip).limit(limit))
    logs = logs_result.scalars().all()
    return logs

@router.get("/api/logs/{log_id}", response_model=ActionLogSchema)
async def get_action_log_api(log_id: int, db: Session = Depends(get_db)):
    """
    Получить детальную информацию о записи лога
    """
    result = await db.execute(select(ActionLog).filter(ActionLog.id == log_id))
    log = result.scalars().first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
