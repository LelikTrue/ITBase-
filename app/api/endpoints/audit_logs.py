from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

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
    query = db.query(ActionLog)

    if user_id is not None:
        query = query.filter(ActionLog.user_id == user_id)
    valid_action_types = ["create", "update", "delete", "login", "logout"]
    if action_type and action_type != "" and action_type in valid_action_types:
        query = query.filter(ActionLog.action_type == action_type)
    elif action_type == "":
        action_type = None

    valid_entity_types = ["Asset", "Device", "Employee", "Location", "Department", "Manufacturer", "AssetType", "DeviceModel", "DeviceStatus"]
    if entity_type and entity_type != "" and entity_type in valid_entity_types:
        query = query.filter(ActionLog.entity_type == entity_type)
    elif entity_type == "":
        entity_type = None

    if entity_id is not None:
        query = query.filter(ActionLog.entity_id == entity_id)
    if start_date:
        query = query.filter(ActionLog.timestamp >= start_date)
    if end_date:
        # Прибавляем один день, чтобы включить все события за указанную дату
        query = query.filter(ActionLog.timestamp < end_date + timedelta(days=1))

    logs = query.order_by(ActionLog.timestamp.desc()).all()

    # Получаем уникальные значения для фильтров
    action_types = db.query(ActionLog.action_type).distinct().all()
    entity_types = db.query(ActionLog.entity_type).distinct().all()

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
    action_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
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
    valid_action_types = ["create", "update", "delete", "login", "logout"]
    if action_type and action_type != "" and action_type in valid_action_types:
        query = query.filter(ActionLog.action_type == action_type)
    elif action_type == "":
        action_type = None
    valid_entity_types = ["Asset", "Device", "Employee", "Location", "Department", "Manufacturer", "AssetType", "DeviceModel", "DeviceStatus"]
    if entity_type and entity_type != "" and entity_type in valid_entity_types:
        query = query.filter(ActionLog.entity_type == entity_type)
    elif entity_type == "":
        entity_type = None
    if entity_id is not None:
        query = query.filter(ActionLog.entity_id == entity_id)
    if start_date:
        query = query.filter(ActionLog.timestamp >= start_date)
    if end_date:
        query = query.filter(ActionLog.timestamp <= end_date)
    
    logs = query.order_by(ActionLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/api/logs/{log_id}", response_model=ActionLogSchema)
async def get_action_log_api(log_id: int, db: Session = Depends(get_db)):
    """
    Получить детальную информацию о записи лога
    """
    log = db.query(ActionLog).filter(ActionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
