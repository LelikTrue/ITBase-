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