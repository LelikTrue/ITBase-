# app/api/endpoints/admin.py

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import (
    AssetType,
    Department,
    Device,
    DeviceModel,
    DeviceStatus,
    Employee,
    Location,
    Manufacturer,
    Tag,
)
from app.services.tag_service import TagService
from app.templating import templates

# Инициализация
logger = logging.getLogger(__name__)
router = APIRouter(tags=['admin'])

tag_service = TagService()

@router.get('/dictionaries', response_class=HTMLResponse)
async def dictionaries_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница управления справочниками"""
    try:
        # --- ИСПРАВЛЕНИЕ: Выполняем запросы последовательно, без asyncio.gather ---

        # 1. Получаем статистику
        stats_results = [
            await db.scalar(select(func.count(AssetType.id))),
            await db.scalar(select(func.count(DeviceModel.id))),
            await db.scalar(select(func.count(DeviceStatus.id))),
            await db.scalar(select(func.count(Manufacturer.id))),
            await db.scalar(select(func.count(Department.id))),
            await db.scalar(select(func.count(Location.id))),
            await db.scalar(select(func.count(Employee.id))),
            await db.scalar(select(func.count(Device.id))),
            await db.scalar(select(func.count(Tag.id))),
        ]

        stats = dict(zip([
            'asset_types', 'device_models', 'device_statuses', 'manufacturers',
            'departments', 'locations', 'employees', 'devices', 'tags'
        ], stats_results, strict=False))

        # 2. Получаем последние записи
        asset_types_res = await db.execute(select(AssetType).order_by(AssetType.id.desc()).limit(3))
        device_models_res = await db.execute(select(DeviceModel).order_by(DeviceModel.id.desc()).limit(3))
        device_statuses_res = await db.execute(select(DeviceStatus).order_by(DeviceStatus.id.desc()).limit(3))

        recent_items = {
            'asset_types': asset_types_res.scalars().all(),
            'device_models': device_models_res.scalars().all(),
            'device_statuses': device_statuses_res.scalars().all(),
        }

        return templates.TemplateResponse('admin/dictionaries_dashboard.html', {
            'request': request,
            'stats': stats,
            'recent_items': recent_items,
            'title': 'Управление справочниками'
        })
    except Exception as e:
        logger.error(f'Ошибка при загрузке дашборда администратора: {e}', exc_info=True)
        return templates.TemplateResponse('error.html', {'request': request, 'error': 'Не удалось загрузить дашборд администратора.'}, status_code=500)

@router.get('/dictionaries/{dictionary_type}', response_class=HTMLResponse)
async def manage_dictionary(
    request: Request,
    dictionary_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Страница управления конкретным справочником"""
    try:
        # Маппинг типов справочников
        dictionary_mapping = {
            'asset-types': {
                'model': AssetType,
                'title': 'Типы активов',
                'fields': ['name', 'description'],
                'template': 'admin/asset_types.html'
            },
            'device-models': {
                'model': DeviceModel,
                'title': 'Модели устройств',
                'fields': ['name', 'manufacturer', 'asset_type', 'description'],
                'template': 'admin/device_models.html'
            },
            'device-statuses': {
                'model': DeviceStatus,
                'title': 'Статусы устройств',
                'fields': ['name', 'description'],
                'template': 'admin/device_statuses.html'
            },
            'manufacturers': {
                'model': Manufacturer,
                'title': 'Производители',
                'fields': ['name', 'description'],
                'template': 'admin/manufacturers.html'
            },
            'departments': {
                'model': Department,
                'title': 'Отделы',
                'fields': ['name', 'description'],
                'template': 'admin/departments.html'
            },
            'locations': {
                'model': Location,
                'title': 'Местоположения',
                'fields': ['name', 'description'],
                'template': 'admin/locations.html'
            },
            'employees': {
                'model': Employee,
                'title': 'Сотрудники',
                'fields': ['first_name', 'last_name', 'patronymic', 'employee_id', 'email'],
                'template': 'admin/employees.html'
            },
            'tags': {
                'model': Tag,
                'title': 'Теги',
                'fields': ['name', 'description'],
                'template': 'admin/tags.html'
            }
        }

        if dictionary_type not in dictionary_mapping:
            raise HTTPException(status_code=404, detail='Справочник не найден')

        config = dictionary_mapping[dictionary_type]
        model = config['model']

        # Получаем все записи
        if dictionary_type == 'device-models':
            # Для моделей устройств нужны связанные данные
            stmt = select(model).options(
                selectinload(model.manufacturer),
                selectinload(model.asset_type)
            ).order_by(model.id.desc())
            items_result = await db.execute(stmt)
            items = items_result.scalars().all()

            # --- ИСПРАВЛЕНИЕ: Убираем asyncio.gather и здесь ---
            # Получаем списки для выпадающих списков последовательно
            manufacturers_res = await db.execute(select(Manufacturer).order_by(Manufacturer.name))
            asset_types_res = await db.execute(select(AssetType).order_by(AssetType.name))

            manufacturers = manufacturers_res.scalars().all()
            asset_types = asset_types_res.scalars().all()
            extra_data = {'manufacturers': manufacturers, 'asset_types': asset_types}
        else:
            items_result = await db.execute(select(model).order_by(model.id.desc()))
            items = items_result.scalars().all()
            extra_data = {}

        return templates.TemplateResponse(config['template'], {
            'request': request,
            'items': items,
            'title': config['title'],
            'dictionary_type': dictionary_type,
            'fields': config['fields'],
            **extra_data
        })
    except Exception as e:
        logger.error(f"Ошибка при загрузке справочника '{dictionary_type}': {e}", exc_info=True)
        return templates.TemplateResponse('error.html', {'request': request, 'error': f"Не удалось загрузить справочник '{dictionary_type}'."}, status_code=500)