from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models.action_log import ActionLog
from app.schemas.audit_log import ActionLog as ActionLogSchema

router = APIRouter()

@router.get("/logs/", response_model=List[ActionLogSchema])
async def get_action_logs(
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
    query = db.query(ActionLog)
    
    if user_id is not None:
        query = query.filter(ActionLog.user_id == user_id)
    if action_type:
        query = query.filter(ActionLog.action_type == action_type)
    if entity_type:
        query = query.filter(ActionLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(ActionLog.entity_id == entity_id)
    if start_date:
        query = query.filter(ActionLog.timestamp >= start_date)
    if end_date:
        query = query.filter(ActionLog.timestamp <= end_date)
    
    logs = query.order_by(ActionLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/logs/{log_id}", response_model=ActionLogSchema)
async def get_action_log(log_id: int, db: Session = Depends(get_db)):
    """
    Получить детальную информацию о записи лога
    """
    log = db.query(ActionLog).filter(ActionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
