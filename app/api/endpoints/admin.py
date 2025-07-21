# app/api/endpoints/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from datetime import datetime

from app.db.database import get_db
from app.models import (
    AssetType, DeviceModel, DeviceStatus, Manufacturer,
    Department, Location, Employee, Device, ActionLog
)
from app.templating import templates

# Инициализация
router = APIRouter(tags=["admin"])

@router.get("/dictionaries", response_class=HTMLResponse)
async def dictionaries_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница управления справочниками"""

    # 1. Define a comprehensive dictionary configuration
    DICTIONARY_CONFIG = {
        "asset-types": {"model": AssetType, "title": "Типы активов", "icon": "bi-collection", "color": "primary", "description": "Категории оборудования"},
        "device-models": {"model": DeviceModel, "title": "Модели устройств", "icon": "bi-laptop", "color": "info", "description": "Конкретные модели оборудования"},
        "device-statuses": {"model": DeviceStatus, "title": "Статусы устройств", "icon": "bi-check-circle", "color": "success", "description": "Состояния оборудования"},
        "manufacturers": {"model": Manufacturer, "title": "Производители", "icon": "bi-building", "color": "warning", "description": "Компании-производители"},
        "departments": {"model": Department, "title": "Отделы", "icon": "bi-diagram-3", "color": "secondary", "description": "Подразделения организации"},
        "locations": {"model": Location, "title": "Местоположения", "icon": "bi-geo-alt", "color": "danger", "description": "Физические расположения"},
        "employees": {"model": Employee, "title": "Сотрудники", "icon": "bi-people", "color": "primary", "description": "Персонал организации"}
    }

    # 2. Get statistics
    stats = {
        "asset_types": db.query(func.count(AssetType.id)).scalar(),
        "device_models": db.query(func.count(DeviceModel.id)).scalar(),
        "device_statuses": db.query(func.count(DeviceStatus.id)).scalar(),
        "manufacturers": db.query(func.count(Manufacturer.id)).scalar(),
        "departments": db.query(func.count(Department.id)).scalar(),
        "locations": db.query(func.count(Location.id)).scalar(),
        "employees": db.query(func.count(Employee.id)).scalar(),
        "devices": db.query(Device).count(),
    }

    # 3. Get last update times from audit log
    last_updates_query = db.query(
        ActionLog.entity_type,
        func.max(ActionLog.timestamp).label('last_updated')
    ).group_by(ActionLog.entity_type).all()
    last_updates = {row.entity_type: row.last_updated for row in last_updates_query}

    # 4. Combine data into a list of dictionaries
    dictionaries_list = []
    for slug, config in DICTIONARY_CONFIG.items():
        model_name = config['model'].__name__
        stat_key = slug.replace('-', '_')
        
        dict_info = {
            "slug": slug,
            "title": config['title'],
            "description": config['description'],
            "icon": config['icon'],
            "color": config['color'],
            "count": stats.get(stat_key, 0),
            "last_updated": last_updates.get(model_name)
        }
        dictionaries_list.append(dict_info)

    # 5. Sort the list by last update time (most recent first)
    min_datetime = datetime.min
    dictionaries_list.sort(key=lambda x: (x['last_updated'] or min_datetime), reverse=True)

    return templates.TemplateResponse("admin/dictionaries_dashboard.html", {
        "request": request,
        "stats": stats,
        "dictionaries": dictionaries_list,
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