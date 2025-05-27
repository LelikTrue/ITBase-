# app/api/endpoints/assets.py

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from app.db.database import get_db
from app.models import Device, DeviceModel, AssetType, DeviceStatus, Department, Location, Employee

# Инициализация APIRouter
router = APIRouter()

# Инициализация Jinja2Templates
# Используем абсолютный путь
templates = Jinja2Templates(directory="/app/templates")

@router.get("/dashboard", response_class=HTMLResponse, name="read_assets")
async def read_assets(request: Request, db: Session = Depends(get_db)):
    """
    Отображает список всех активов на дашборде.
    """
    try:
        assets = db.execute(
            select(Device)
            .options(
                joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
                joinedload(Device.asset_type),
                joinedload(Device.status),
                joinedload(Device.department),
                joinedload(Device.location),
                joinedload(Device.employee)
            )
            .order_by(Device.added_at.desc())
            .limit(10)
        ).scalars().all()

        device_types_count = db.execute(
            select(AssetType.name, func.count(Device.id))
            .join(Device, Device.asset_type_id == AssetType.id)
            .group_by(AssetType.name)
        ).all()

        device_statuses_count = db.execute(
            select(DeviceStatus.name, func.count(Device.id))
            .join(Device, Device.status_id == DeviceStatus.id)
            .group_by(DeviceStatus.name)
        ).all()

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        assets = []
        device_types_count = []
        device_statuses_count = []

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "assets": assets, # Передаем 'assets'
            "device_types_count": device_types_count,
            "device_statuses_count": device_statuses_count,
            "title": "IT Asset Dashboard" # Добавим title для шаблона
        }
    )

@router.get("/add", response_class=HTMLResponse, name="add_asset_form")
async def add_asset_form(request: Request):
    """
    Отображает форму для добавления нового актива.
    """
    # Добавьте пустой объект device для рендеринга формы добавления
    # А также списки для выпадающих меню
    # (В реальном приложении эти списки нужно будет загружать из БД)
    # Здесь просто заглушки для начала
    device = type('Device', (object,), {
        'id': None, 'inventory_number': None, 'serial_number': None,
        'mac_address': None, 'ip_address': None, 'asset_type_id': None,
        'device_model_id': None, 'status_id': None, 'department_id': None,
        'location_id': None, 'employee_id': None, 'notes': None, 'source': None,
        'purchase_date': None, 'warranty_end_date': None, 'price': None,
        'image_url': None, 'acquisition_method': None, 'condition': None,
        'assigned_date': None, 'return_date': None, 'last_service_date': None,
        'next_service_date': None
    })() # Создаем "пустой" объект Device

    # Вам нужно будет загрузить эти данные из БД для реального заполнения форм
    # Пока оставляем пустыми или с заглушками для теста
    asset_types = []
    device_models = []
    device_statuses = []
    departments = []
    locations = []
    employees = []

    return templates.TemplateResponse(
        "add_asset.html", # Имя файла шаблона, после переименования
        {
            "request": request,
            "device": device, # Передаем объект device
            "asset_types": asset_types,
            "device_models": device_models,
            "device_statuses": device_statuses,
            "departments": departments,
            "locations": locations,
            "employees": employees
        }
    )

# Добавьте заглушки для роутов, которые используются в шаблоне add_asset.html
# Эти роуты будут принимать данные из формы и сохранять их в БД
@router.post("/create", name="create_asset")
async def create_asset():
    raise HTTPException(status_code=501, detail="Not Implemented: create_asset")

@router.get("/edit/{device_id}", response_class=HTMLResponse, name="edit_asset")
async def edit_asset(request: Request, device_id: int):
    raise HTTPException(status_code=501, detail=f"Not Implemented: edit_asset for ID {device_id}")

@router.post("/update/{device_id}", name="update_asset")
async def update_asset(device_id: int):
    raise HTTPException(status_code=501, detail=f"Not Implemented: update_asset for ID {device_id}")

@router.post("/delete/{device_id}", name="delete_asset")
async def delete_asset(device_id: int):
    raise HTTPException(status_code=501, detail=f"Not Implemented: delete_asset for ID {device_id}")