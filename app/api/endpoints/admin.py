# app/api/endpoints/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from app.db.database import get_db
from app.models import (
    AssetType, DeviceModel, DeviceStatus, Manufacturer, 
    Department, Location, Employee, Device
)

# Инициализация
router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/dictionaries", response_class=HTMLResponse)
async def dictionaries_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница управления справочниками"""
    
    # Получаем статистику по всем справочникам
    stats = {
        "asset_types": db.query(AssetType).count(),
        "device_models": db.query(DeviceModel).count(),
        "device_statuses": db.query(DeviceStatus).count(),
        "manufacturers": db.query(Manufacturer).count(),
        "departments": db.query(Department).count(),
        "locations": db.query(Location).count(),
        "employees": db.query(Employee).count(),
        "devices": db.query(Device).count(),
    }
    
    # Получаем последние добавленные записи
    recent_items = {
        "asset_types": db.query(AssetType).order_by(AssetType.id.desc()).limit(3).all(),
        "device_models": db.query(DeviceModel).order_by(DeviceModel.id.desc()).limit(3).all(),
        "device_statuses": db.query(DeviceStatus).order_by(DeviceStatus.id.desc()).limit(3).all(),
    }
    
    return templates.TemplateResponse("admin/dictionaries_dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_items": recent_items,
        "title": "Управление справочниками"
    })

@router.get("/dictionaries/{dictionary_type}", response_class=HTMLResponse)
async def manage_dictionary(
    request: Request, 
    dictionary_type: str, 
    db: Session = Depends(get_db)
):
    """Страница управления конкретн��м справочником"""
    
    # Маппинг типов справочников
    dictionary_mapping = {
        "asset-types": {
            "model": AssetType,
            "title": "Типы активов",
            "fields": ["name", "description"],
            "template": "admin/asset_types.html"
        },
        "device-models": {
            "model": DeviceModel,
            "title": "Модели устройств", 
            "fields": ["name", "manufacturer", "asset_type", "description"],
            "template": "admin/device_models.html"
        },
        "device-statuses": {
            "model": DeviceStatus,
            "title": "Статусы устройств",
            "fields": ["name", "description"],
            "template": "admin/device_statuses.html"
        },
        "manufacturers": {
            "model": Manufacturer,
            "title": "Производители",
            "fields": ["name", "description"],
            "template": "admin/manufacturers.html"
        },
        "departments": {
            "model": Department,
            "title": "Отделы",
            "fields": ["name", "description"],
            "template": "admin/departments.html"
        },
        "locations": {
            "model": Location,
            "title": "Местоположения",
            "fields": ["name", "description"],
            "template": "admin/locations.html"
        },
        "employees": {
            "model": Employee,
            "title": "Сотрудники",
            "fields": ["first_name", "last_name", "patronymic", "employee_id", "email"],
            "template": "admin/employees.html"
        }
    }
    
    if dictionary_type not in dictionary_mapping:
        raise HTTPException(status_code=404, detail="Справочник не найден")
    
    config = dictionary_mapping[dictionary_type]
    model = config["model"]
    
    # Получаем все записи
    if dictionary_type == "device-models":
        # Для моделей устройств нужны связанные данные
        items = db.query(model).join(Manufacturer, model.manufacturer_id == Manufacturer.id, isouter=True)\
                              .join(AssetType, model.asset_type_id == AssetType.id, isouter=True)\
                              .all()
        # Получаем списки для выпадающих списков
        manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
        asset_types = db.query(AssetType).order_by(AssetType.name).all()
        extra_data = {"manufacturers": manufacturers, "asset_types": asset_types}
    else:
        items = db.query(model).order_by(model.id.desc()).all()
        extra_data = {}
    
    return templates.TemplateResponse(config["template"], {
        "request": request,
        "items": items,
        "title": config["title"],
        "dictionary_type": dictionary_type,
        "fields": config["fields"],
        **extra_data
    })

@router.get("/api/dictionaries/stats")
async def get_dictionaries_stats(db: Session = Depends(get_db)):
    """API для получения статистики справочников"""
    
    stats = {
        "asset_types": {
            "count": db.query(AssetType).count(),
            "used": db.query(func.count(func.distinct(Device.asset_type_id))).scalar() or 0
        },
        "device_models": {
            "count": db.query(DeviceModel).count(),
            "used": db.query(func.count(func.distinct(Device.device_model_id))).scalar() or 0
        },
        "device_statuses": {
            "count": db.query(DeviceStatus).count(),
            "used": db.query(func.count(func.distinct(Device.status_id))).scalar() or 0
        },
        "manufacturers": {
            "count": db.query(Manufacturer).count(),
            "used": db.query(func.count(func.distinct(DeviceModel.manufacturer_id))).scalar() or 0
        },
        "departments": {
            "count": db.query(Department).count(),
            "used": db.query(func.count(func.distinct(Device.department_id))).scalar() or 0
        },
        "locations": {
            "count": db.query(Location).count(),
            "used": db.query(func.count(func.distinct(Device.location_id))).scalar() or 0
        },
        "employees": {
            "count": db.query(Employee).count(),
            "used": db.query(func.count(func.distinct(Device.employee_id))).scalar() or 0
        }
    }
    
    return stats

# CRUD endpoints для справочников

@router.post("/dictionaries/{dictionary_type}")
async def create_dictionary_item(
    dictionary_type: str,
    item_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Создание нового элемента справочника"""
    
    # Маппинг типов справочников
    dictionary_mapping = {
        "asset-types": AssetType,
        "device-models": DeviceModel,
        "device-statuses": DeviceStatus,
        "manufacturers": Manufacturer,
        "departments": Department,
        "locations": Location,
        "employees": Employee
    }
    
    if dictionary_type not in dictionary_mapping:
        raise HTTPException(status_code=404, detail="Справочник не найден")
    
    model = dictionary_mapping[dictionary_type]
    
    try:
        # Создаем новый объект
        new_item = model(**item_data)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        return {"status": "success", "id": new_item.id, "message": "Элемент успешно создан"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при создании: {str(e)}")

@router.put("/dictionaries/{dictionary_type}/{item_id}")
async def update_dictionary_item(
    dictionary_type: str,
    item_id: int,
    item_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Обновление элемента справочника"""
    
    # Маппинг типов справочников
    dictionary_mapping = {
        "asset-types": AssetType,
        "device-models": DeviceModel,
        "device-statuses": DeviceStatus,
        "manufacturers": Manufacturer,
        "departments": Department,
        "locations": Location,
        "employees": Employee
    }
    
    if dictionary_type not in dictionary_mapping:
        raise HTTPException(status_code=404, detail="Справочник не найден")
    
    model = dictionary_mapping[dictionary_type]
    
    # Находим элемент
    item = db.query(model).filter(model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Элемент не найден")
    
    try:
        # Обновляем поля
        for key, value in item_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        db.commit()
        db.refresh(item)
        
        return {"status": "success", "message": "Элемент успешно обновлен"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении: {str(e)}")

@router.delete("/dictionaries/{dictionary_type}/{item_id}")
async def delete_dictionary_item(
    dictionary_type: str,
    item_id: int,
    db: Session = Depends(get_db)
):
    """Удаление элемента справочника"""
    
    # Маппинг типов справочников
    dictionary_mapping = {
        "asset-types": AssetType,
        "device-models": DeviceModel,
        "device-statuses": DeviceStatus,
        "manufacturers": Manufacturer,
        "departments": Department,
        "locations": Location,
        "employees": Employee
    }
    
    if dictionary_type not in dictionary_mapping:
        raise HTTPException(status_code=404, detail="Справочник не найден")
    
    model = dictionary_mapping[dictionary_type]
    
    # Находим элемент
    item = db.query(model).filter(model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Элемент не найден")
    
    try:
        # Проверяем, используется ли элемент
        if dictionary_type == "device-statuses":
            usage_count = db.query(Device).filter(Device.status_id == item_id).count()
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Нельзя удалить статус, используемый в {usage_count} устройствах"
                )
        elif dictionary_type == "manufacturers":
            usage_count = db.query(DeviceModel).filter(DeviceModel.manufacturer_id == item_id).count()
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Нельзя удалить производителя, используемого в {usage_count} моделях"
                )
        elif dictionary_type == "asset-types":
            usage_count = db.query(Device).filter(Device.asset_type_id == item_id).count()
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Нельзя удалить тип актива, используемый в {usage_count} устройствах"
                )
        
        db.delete(item)
        db.commit()
        
        return {"status": "success", "message": "Элемент успешно удален"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при удалении: {str(e)}")