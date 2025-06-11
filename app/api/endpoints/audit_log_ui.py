from fastapi import APIRouter, Request, Depends, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.db.database import get_db
from app.models.action_log import ActionLog
from app.config import TEMPLATES_DIR
from fastapi.templating import Jinja2Templates
from app.main import flash

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@router.get("/logs", response_class=HTMLResponse, name="view_logs")
async def view_logs(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Отображает страницу с логами действий с возможностью фильтрации
    """
    try:
        query = db.query(ActionLog)
        
        # Применяем фильтры
        if user_id is not None:
            query = query.filter(ActionLog.user_id == user_id)
        if action_type:
            query = query.filter(ActionLog.action_type == action_type)
        if entity_type:
            query = query.filter(ActionLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.filter(ActionLog.entity_id == entity_id)
        if start_date:
            # Если start_date не содержит временную зону, добавляем UTC
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            query = query.filter(ActionLog.timestamp >= start_date)
        if end_date:
            # Если end_date не содержит временную зону, добавляем UTC
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            # Добавляем 1 день к конечной дате, чтобы включить весь день
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(ActionLog.timestamp <= end_date)
        
        # Получаем логи с сортировкой по времени (новые сверху)
        logs = query.order_by(ActionLog.timestamp.desc()).offset(skip).limit(limit).all()
        
        # Получаем уникальные значения для фильтров
        action_types = db.query(ActionLog.action_type).distinct().all()
        entity_types = db.query(ActionLog.entity_type).distinct().all()
        
        # Преобразуем фильтры для отображения в форме
        filters = {
            "user_id": user_id,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "start_date": start_date.date() if start_date else None,
            "end_date": end_date.date() if end_date else None,
        }
        
        return templates.TemplateResponse(
            "audit_logs.html",
            {
                "request": request,
                "logs": logs,
                "action_types": [t[0] for t in action_types if t[0]],
                "entity_types": [t[0] for t in entity_types if t[0]],
                "filters": filters,
                "title": "Журнал действий"
            }
        )
        
    except Exception as e:
        # Логируем ошибку
        print(f"Ошибка при получении логов: {str(e)}")
        
        # Добавляем сообщение об ошибке
        flash(request, f"Произошла ошибка при загрузке логов: {str(e)}", "danger")
        
        # Перенаправляем на главную страницу
        return RedirectResponse(
            url=request.url_for("read_assets"),
            status_code=status.HTTP_303_SEE_OTHER
        )
