import logging
from datetime import datetime, date, timezone
from typing import Optional

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.action_log import ActionLog
from app.templating import templates
from app.flash import flash

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Audit Logs"])


# ===============================================================
# HTML Эндпоинт для отображения страницы журнала аудита
# ===============================================================
@router.get("/audit-logs", response_class=HTMLResponse, name="view_audit_logs_page")
async def view_audit_logs_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    entity_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    try:
        base_query = select(ActionLog)

        filters = {
            "action_type": action_type, "entity_type": entity_type, "user_id": user_id,
            "entity_id": entity_id, "start_date": start_date, "end_date": end_date,
        }
        if user_id is not None: base_query = base_query.filter(ActionLog.user_id == user_id)
        if action_type: base_query = base_query.filter(ActionLog.action_type == action_type)
        if entity_type: base_query = base_query.filter(ActionLog.entity_type == entity_type)
        if entity_id is not None: base_query = base_query.filter(ActionLog.entity_id == entity_id)
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            base_query = base_query.filter(ActionLog.timestamp >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
            base_query = base_query.filter(ActionLog.timestamp <= end_datetime)

        count_query = select(func.count()).select_from(base_query.subquery())
        total_logs = (await db.execute(count_query)).scalar_one()

        total_pages = (total_logs + page_size - 1) // page_size if page_size > 0 else 1

        logs_query = base_query.order_by(ActionLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
        logs_result = await db.execute(logs_query)
        logs = logs_result.scalars().all()

        action_types_res = await db.execute(select(ActionLog.action_type).distinct())
        entity_types_res = await db.execute(select(ActionLog.entity_type).distinct())

        query_params = request.query_params._dict.copy()
        query_params.pop("page", None)

        context = {
            "request": request, "title": "Журнал действий", "logs": logs,
            "page": page, "page_size": page_size, "total_pages": total_pages,
            "total_logs": total_logs,
            "action_types": [item for item in action_types_res.scalars().all() if item],
            "entity_types": [item for item in entity_types_res.scalars().all() if item],
            "filters": filters, "query_params": query_params, "endpoint_name": "view_audit_logs_page"
        }
        return templates.TemplateResponse("audit_logs.html", context)

    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы журнала аудита: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": "Не удалось загрузить журнал действий."}, status_code=500)


# ===============================================================
# API Эндпоинт для удаления записи лога (используется JS)
# ===============================================================
@router.delete("/api/audit-logs/{log_id}", status_code=204)
async def delete_log_entry(log_id: int, db: AsyncSession = Depends(get_db)):
    log_entry = await db.get(ActionLog, log_id)
    if not log_entry:
        return JSONResponse(status_code=404, content={"detail": "Log entry not found"})
    
    logger.info(f"Deleting log entry with ID: {log_id}")
    await db.delete(log_entry)
    await db.commit()
    return None