from fastapi import APIRouter, Depends, HTTPException, Request, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.db.database import get_db
from app.models import ActionLog
from app.schemas.audit_log import ActionLog as ActionLogSchema
from app.templating import templates
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Action Logs"])

@router.get("/action-logs", name="view_action_logs_page", response_class=templates.TemplateResponse)
async def view_logs_page(
    request: Request,
    db: Session = Depends(get_db),
    action_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Отображает страницу журнала действий с фильтрацией."""
    try:
        query = db.query(ActionLog)

        # Apply filters
        if user_id and user_id.isdigit():
            query = query.filter(ActionLog.user_id == int(user_id))

        if action_type:
            query = query.filter(ActionLog.action_type == action_type)

        if entity_type:
            query = query.filter(ActionLog.entity_type == entity_type)

        if entity_id and entity_id.isdigit():
            query = query.filter(ActionLog.entity_id == int(entity_id))

        # Handle date filters
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(ActionLog.timestamp >= start_date_obj)
            except ValueError:
                start_date = None

        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(ActionLog.timestamp < end_date_obj)
            except ValueError:
                end_date = None

        # Execute query
        logs = query.order_by(ActionLog.timestamp.desc()).all()

        # Get unique values for filters
        action_types_result = db.query(ActionLog.action_type).distinct().all()
        entity_types_result = db.query(ActionLog.entity_type).distinct().all()

        context = {
            "request": request,
            "title": "Журнал действий",
            "logs": logs,
            "action_types": sorted([item[0] for item in action_types_result if item[0]]),
            "entity_types": sorted([item[0] for item in entity_types_result if item[0]]),
            "filters": {
                "action_type": action_type or "",
                "entity_type": entity_type or "",
                "user_id": user_id or "",
                "entity_id": entity_id or "",
                "start_date": start_date or "",
                "end_date": end_date or "",
            }
        }
        return templates.TemplateResponse("admin/action_logs.html", context)

    except Exception as e:
        logger.error(f"Error in action logs page: {str(e)}", exc_info=True)
        return templates.TemplateResponse("admin/action_logs.html", {
            "request": request,
            "title": "Ошибка",
            "error": f"Произошла ошибка при загрузке журнала: {str(e)}",
            "logs": [],
            "action_types": [],
            "entity_types": [],
            "filters": {}
        })

@router.delete("/action-logs/{log_id}", status_code=204)
async def delete_action_log(log_id: int, db: Session = Depends(get_db)):
    """Удаляет запись из журнала действий (используется со страницы)."""
    log = db.query(ActionLog).filter(ActionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    try:
        db.delete(log)
        db.commit()
        logger.info(f"Deleted log entry with ID: {log_id}")
        return Response(status_code=204)
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting log entry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting log entry: {str(e)}")