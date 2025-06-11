from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.database import get_db
from app.models.device import Device
from app.services.audit_log_service import log_action

router = APIRouter()

@router.post("/devices/{device_id}/delete")
async def delete_device(
    request: Request,
    device_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = {"id": 1}  # Заглушка, замените на реальную аутентификацию
):
    """
    Удаляет устройство по ID.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        request.session["message"] = {
            "type": "danger",
            "text": f"Устройство с ID {device_id} не найдено!"
        }
        return RedirectResponse(
            url=request.url_for("read_assets"),
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    try:
        # Сохраняем данные перед удалением для лога
        device_data = {
            "inventory_number": device.inventory_number,
            "device_model_id": device.device_model_id,
            "status_id": device.status_id
        }
        
        # Логируем удаление устройства
        await log_action(
            db=db,
            user_id=current_user["id"],
            action_type="delete",
            entity_type="Device",
            entity_id=device_id,
            details=device_data
        )
        
        db.delete(device)
        db.commit()
        
        request.session["message"] = {
            "type": "success",
            "text": f"Устройство {device.inventory_number} успешно удалено!"
        }
        
    except Exception as e:
        db.rollback()
        request.session["message"] = {
            "type": "danger",
            "text": f"Ошибка при удалении устройства: {str(e)}"
        }
    
    return RedirectResponse(
        url=request.url_for("read_assets"),
        status_code=status.HTTP_303_SEE_OTHER
    )
