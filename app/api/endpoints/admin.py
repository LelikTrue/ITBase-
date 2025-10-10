# app/api/endpoints/admin.py

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.templating import templates
from typing import Dict, Any
import asyncio
import logging

from app.db.database import get_db
from app.models import (
    AssetType, DeviceModel, DeviceStatus, Manufacturer, 
    Department, Location, Employee, Device
)

# Инициализация
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dictionaries", response_class=HTMLResponse)
async def dictionaries_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница управления справочниками"""
    try:
        # Асинхронно получаем статистику и последние записи
        stats_queries = [
            db.scalar(select(func.count(AssetType.id))),
            db.scalar(select(func.count(DeviceModel.id))),
            db.scalar(select(func.count(DeviceStatus.id))),
            db.scalar(select(func.count(Manufacturer.id))),
            db.scalar(select(func.count(Department.id))),
            db.scalar(select(func.count(Location.id))),
            db.scalar(select(func.count(Employee.id))),
            db.scalar(select(func.count(Device.id))),
        ]
        
        recent_items_queries = [
            db.execute(select(AssetType).order_by(AssetType.id.desc()).limit(3)),
            db.execute(select(DeviceModel).order_by(DeviceModel.id.desc()).limit(3)),
            db.execute(select(DeviceStatus).order_by(DeviceStatus.id.desc()).limit(3)),
        ]

        results = await asyncio.gather(*stats_queries, *recent_items_queries)
        
        stats_results = results[:8]
        recent_items_results = results[8:]

        stats = dict(zip([
            "asset_types", "device_models", "device_statuses", "manufacturers",
            "departments", "locations", "employees", "devices"
        ], stats_results))

        recent_items = {
            "asset_types": recent_items_results[0].scalars().all(),
            "device_models": recent_items_results[1].scalars().all(),
            "device_statuses": recent_items_results[2].scalars().all(),
        }
        
        return templates.TemplateResponse("admin/dictionaries_dashboard.html", {
            "request": request,
            "stats": stats,
            "recent_items": recent_items,
            "title": "Управление справочниками"
        })
    except Exception as e:
        logger.error(f"Ошибка при загрузке дашборда администратора: {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": "Не удалось загрузить дашборд администратора."}, status_code=500)

@router.get("/dictionaries/{dictionary_type}", response_class=HTMLResponse)
async def manage_dictionary(
    request: Request, 
    dictionary_type: str, 
    db: AsyncSession = Depends(get_db)
):
    """Страница управления конкретн��м справочником"""
    try:
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
            stmt = select(model).options(
                selectinload(model.manufacturer),
                selectinload(model.asset_type)
            ).order_by(model.id.desc())
            items_result = await db.execute(stmt)
            items = items_result.scalars().all()

            # Получаем списки для выпадающих списков
            manufacturers_res, asset_types_res = await asyncio.gather(
                db.execute(select(Manufacturer).order_by(Manufacturer.name)),
                db.execute(select(AssetType).order_by(AssetType.name))
            )
            manufacturers = manufacturers_res.scalars().all()
            asset_types = asset_types_res.scalars().all()
            extra_data = {"manufacturers": manufacturers, "asset_types": asset_types}
        else:
            items_result = await db.execute(select(model).order_by(model.id.desc()))
            items = items_result.scalars().all()
            extra_data = {}
        
        return templates.TemplateResponse(config["template"], {
            "request": request,
            "items": items,
            "title": config["title"],
            "dictionary_type": dictionary_type,
            "fields": config["fields"],
            **extra_data
        })
    except Exception as e:
        logger.error(f"Ошибка при загрузке справочника '{dictionary_type}': {e}", exc_info=True)
        return templates.TemplateResponse("error.html", {"request": request, "error": f"Не удалось загрузить справочник '{dictionary_type}'."}, status_code=500)

@router.get("/api/dictionaries/stats")
async def get_dictionaries_stats(db: AsyncSession = Depends(get_db)):
    """API для получения статистики справочников"""
    try:
        queries = {
            "asset_types": [select(func.count(AssetType.id)), select(func.count(func.distinct(Device.asset_type_id)))],
            "device_models": [select(func.count(DeviceModel.id)), select(func.count(func.distinct(Device.device_model_id)))],
            "device_statuses": [select(func.count(DeviceStatus.id)), select(func.count(func.distinct(Device.status_id)))],
            "manufacturers": [select(func.count(Manufacturer.id)), select(func.count(func.distinct(DeviceModel.manufacturer_id)))],
            "departments": [select(func.count(Department.id)), select(func.count(func.distinct(Device.department_id)))],
            "locations": [select(func.count(Location.id)), select(func.count(func.distinct(Device.location_id)))],
            "employees": [select(func.count(Employee.id)), select(func.count(func.distinct(Device.employee_id)))],
        }

        stats = {}
        for key, (count_q, used_q) in queries.items():
            count_res, used_res = await asyncio.gather(
                db.execute(count_q),
                db.execute(used_q)
            )
            stats[key] = {
                "count": count_res.scalar_one(),
                "used": used_res.scalar_one() or 0
            }
        
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики справочников: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при получении статистики.")

# CRUD endpoints для справочников

@router.post("/dictionaries/{dictionary_type}")
async def create_dictionary_item(
    dictionary_type: str,
    item_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
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
        await db.commit()
        await db.refresh(new_item)
        
        return {"status": "success", "id": new_item.id, "message": "Элемент успешно создан"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при создании элемента в справочнике '{dictionary_type}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.put("/dictionaries/{dictionary_type}/{item_id}")
async def update_dictionary_item(
    dictionary_type: str,
    item_id: int,
    item_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
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
    item = await db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Элемент не найден")
    
    try:
        # Обновляем поля
        for key, value in item_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        await db.commit()
        await db.refresh(item)
        
        return {"status": "success", "message": "Элемент успешно обновлен"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при обновлении элемента {item_id} в справочнике '{dictionary_type}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.delete("/dictionaries/{dictionary_type}/{item_id}")
async def delete_dictionary_item(
    dictionary_type: str,
    item_id: int,
    db: AsyncSession = Depends(get_db)
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
    item = await db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Элемент не найден")
    
    try:
        # Проверяем, используется ли элемент
        if dictionary_type == "device-statuses":
            usage_count = await db.scalar(select(func.count(Device.id)).where(Device.status_id == item_id))
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Нельзя удалить статус, используемый в {usage_count} устройствах"
                )
        elif dictionary_type == "manufacturers":
            usage_count = await db.scalar(select(func.count(DeviceModel.id)).where(DeviceModel.manufacturer_id == item_id))
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Нельзя удалить производителя, используемого в {usage_count} моделях"
                )
        elif dictionary_type == "asset-types":
            usage_count = await db.scalar(select(func.count(Device.id)).where(Device.asset_type_id == item_id))
            if usage_count > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Нельзя удалить тип актива, используемый в {usage_count} устройствах"
                )
        
        await db.delete(item)
        await db.commit()
        
        return {"status": "success", "message": "Элемент успешно удален"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при удалении элемента {item_id} из справочника '{dictionary_type}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")