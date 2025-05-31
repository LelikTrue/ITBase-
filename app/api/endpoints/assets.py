# app/api/endpoints/assets.py

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
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
    Отображает дашборд со списком активов и статистикой.
    """
    try:
        # Получаем сообщение из сессии, если оно есть
        message = request.session.pop("message", None)
        
        # Получаем список активов с жадной загрузкой связанных данных
        devices = db.query(Device).options(
            joinedload(Device.asset_type),
            joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
            joinedload(Device.status),
            joinedload(Device.department),
            joinedload(Device.employee)
        ).order_by(Device.updated_at.desc()).limit(50).all()
        
        # Получаем статистику по типам устройств
        device_types_count = db.execute(
            select(AssetType.name, func.count(Device.id))
            .join(Device, Device.asset_type_id == AssetType.id)
            .group_by(AssetType.name)
        ).all()
        
        # Получаем статистику по статусам устройств
        device_statuses_count = db.execute(
            select(DeviceStatus.name, func.count(Device.id))
            .join(Device, Device.status_id == DeviceStatus.id)
            .group_by(DeviceStatus.name)
        ).all()
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "devices": devices,
                "device_types_count": device_types_count,
                "device_statuses_count": device_statuses_count,
                "message": message,
                "title": "IT Asset Tracker - Дашборд"
            }
        )
        
    except Exception as e:
        print(f"Error in read_assets: {e}")
        # В случае ошибки возвращаем пустые данные
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "devices": [],
                "device_types_count": [],
                "device_statuses_count": [],
                "message": {"type": "danger", "text": f"Ошибка при загрузке данных: {str(e)}"},
                "title": "Ошибка - IT Asset Tracker"
            }
        )

@router.get("/add", response_class=HTMLResponse, name="add_asset_form")
async def add_asset_form(request: Request, db: Session = Depends(get_db)):
    """
    Отображает форму для добавления нового актива.
    """
    # Создаем пустой объект device для рендеринга формы
    device = type('Device', (object,), {
        'id': None, 'inventory_number': None, 'serial_number': None,
        'mac_address': None, 'ip_address': None, 'asset_type_id': None,
        'device_model_id': None, 'status_id': None, 'department_id': None,
        'location_id': None, 'employee_id': None, 'notes': None, 'source': "",
        'purchase_date': None, 'warranty_end_date': None, 'price': None,
        'manufacturer_id': None, 'supplier_id': None
    })()
    
    # Загружаем данные для выпадающих списков из базы
    asset_types = db.query(AssetType).all()
    device_models = db.query(DeviceModel).options(joinedload(DeviceModel.manufacturer)).all()
    device_statuses = db.query(DeviceStatus).all()
    departments = db.query(Department).all()
    locations = db.query(Location).all()
    employees = db.query(Employee).all()
    
    # Получаем уникальных производителей из моделей устройств
    manufacturers = list({model.manufacturer for model in device_models if model.manufacturer})
    
    # Загружаем поставщиков (если есть отдельная модель Supplier)
    try:
        from app.models import Supplier
        suppliers = db.query(Supplier).all()
    except ImportError:
        suppliers = []
    
    return templates.TemplateResponse(
        "add_asset.html",
        {
            "request": request,
            "device": device,
            "asset_types": asset_types,
            "device_models": device_models,
            "statuses": device_statuses,
            "departments": departments,
            "locations": locations,
            "employees": employees,
            "manufacturers": manufacturers,
            "suppliers": suppliers,
            "title": "Добавить актив - IT Asset Tracker"
        }
    )

# Добавьте заглушки для роутов, которые используются в шаблоне add_asset.html
# Эти роуты будут принимать данные из формы и сохранять их в БД
from fastapi.responses import RedirectResponse
from fastapi import Form, status
from datetime import datetime

def _parse_form_data(
    inventory_number: str,
    serial_number: Optional[str],
    mac_address: Optional[str],
    ip_address: Optional[str],
    asset_type_id: str,
    device_model_id: str,
    status_id: str,
    department_id: Optional[str],
    location_id: Optional[str],
    employee_id: Optional[str],
    notes: Optional[str],
    source: str,
    purchase_date: Optional[str],
    warranty_end_date: Optional[str],
    price: Optional[str],
    manufacturer_id: Optional[str] = None,
    supplier_id: Optional[str] = None
):
    """Парсит и валидирует данные из формы."""
    # Обработка числовых полей
    def to_int(value: Optional[str]) -> Optional[int]:
        return int(value) if value and value.strip() else None
        
    def to_float(value: Optional[str]) -> Optional[float]:
        return float(value) if value and value.strip() else None
    
    # Обработка дат
    def parse_date(date_str: Optional[str]) -> Optional[date]:
        if not date_str or not date_str.strip():
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None
    
    return {
        'inventory_number': inventory_number.strip(),
        'serial_number': serial_number.strip() if serial_number else None,
        'mac_address': mac_address.strip() if mac_address else None,
        'ip_address': ip_address.strip() if ip_address else None,
        'asset_type_id': int(asset_type_id),
        'device_model_id': int(device_model_id),
        'status_id': int(status_id),
        'department_id': to_int(department_id),
        'location_id': to_int(location_id),
        'employee_id': to_int(employee_id),
        'notes': notes.strip() if notes else None,
        'source': source.strip(),
        'purchase_date': parse_date(purchase_date),
        'warranty_end_date': parse_date(warranty_end_date),
        'price': to_float(price),
        'manufacturer_id': to_int(manufacturer_id),
        'supplier_id': to_int(supplier_id)
    }

@router.post("/create", name="create_asset")
async def create_asset(
    request: Request,
    inventory_number: str = Form(...),
    serial_number: Optional[str] = Form(None),
    mac_address: Optional[str] = Form(None),
    ip_address: Optional[str] = Form(None),
    asset_type_id: str = Form(...),
    device_model_id: str = Form(...),
    status_id: str = Form(...),
    department_id: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    employee_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    source: str = Form(...),
    purchase_date: Optional[str] = Form(None),
    warranty_end_date: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    manufacturer_id: Optional[str] = Form(None),
    supplier_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Обрабатывает форму создания нового актива.
    """
    try:
        # Парсим и валидируем данные
        form_data = _parse_form_data(
            inventory_number=inventory_number,
            serial_number=serial_number,
            mac_address=mac_address,
            ip_address=ip_address,
            asset_type_id=asset_type_id,
            device_model_id=device_model_id,
            status_id=status_id,
            department_id=department_id,
            location_id=location_id,
            employee_id=employee_id,
            notes=notes,
            source=source,
            purchase_date=purchase_date,
            warranty_end_date=warranty_end_date,
            price=price,
            manufacturer_id=manufacturer_id,
            supplier_id=supplier_id
        )
        
        # Создаем новое устройство
        device = Device(
            **form_data,
            added_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Устанавливаем сообщение об успехе
        request.session["message"] = {"type": "success", "text": "Актив успешно добавлен!"}
        
        # Перенаправляем на дашборд
        return RedirectResponse(
            url=request.url_for("read_assets"),
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        db.rollback()
        # Устанавливаем сообщение об ошибке
        request.session["message"] = {"type": "danger", "text": f"Ошибка при добавлении актива: {str(e)}"}
        
        # Возвращаем обратно на форму с сохраненными данными
        return RedirectResponse(
            url=request.url_for("add_asset_form"),
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/assets/{device_id}/edit", response_class=HTMLResponse, name="edit_asset")
async def edit_asset(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Отображает форму редактирования существующего актива.
    """
    # Загружаем устройство с связанными данными
    device = db.query(Device).options(
        joinedload(Device.asset_type),
        joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
        joinedload(Device.status),
        joinedload(Device.department),
        joinedload(Device.location),
        joinedload(Device.employee)
    ).filter(Device.id == device_id).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    
    # Загружаем данные для выпадающих списков
    asset_types = db.query(AssetType).all()
    device_models = db.query(DeviceModel).options(joinedload(DeviceModel.manufacturer)).all()
    device_statuses = db.query(DeviceStatus).all()
    departments = db.query(Department).all()
    locations = db.query(Location).all()
    employees = db.query(Employee).all()
    
    # Получаем уникальных производителей из моделей устройств
    manufacturers = list({model.manufacturer for model in device_models if model.manufacturer})
    
    # Загружаем поставщиков (если есть отдельная модель Supplier)
    try:
        from app.models import Supplier
        suppliers = db.query(Supplier).all()
    except ImportError:
        suppliers = []
    
    return templates.TemplateResponse(
        "add_asset.html",  # Используем тот же шаблон, что и для добавления
        {
            "request": request,
            "device": device,
            "asset_types": asset_types,
            "device_models": device_models,
            "statuses": device_statuses,  # Исправлено с device_statuses на statuses для единообразия
            "departments": departments,
            "locations": locations,
            "employees": employees,
            "manufacturers": manufacturers,
            "suppliers": suppliers,
            "title": f"Редактировать актив #{device.id} - IT Asset Tracker"
        }
    )

@router.put("/update/{device_id}", name="update_asset")
async def update_asset(
    request: Request,
    device_id: int,
    inventory_number: str = Form(...),
    serial_number: Optional[str] = Form(None),
    mac_address: Optional[str] = Form(None),
    ip_address: Optional[str] = Form(None),
    asset_type_id: str = Form(...),
    device_model_id: str = Form(...),
    status_id: str = Form(...),
    department_id: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    employee_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    source: str = Form(...),
    purchase_date: Optional[str] = Form(None),
    warranty_end_date: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    manufacturer_id: Optional[str] = Form(None),
    supplier_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Обрабатывает обновление существующего актива.
    """
    try:
        # Парсим и валидируем данные
        form_data = _parse_form_data(
            inventory_number=inventory_number,
            serial_number=serial_number,
            mac_address=mac_address,
            ip_address=ip_address,
            asset_type_id=asset_type_id,
            device_model_id=device_model_id,
            status_id=status_id,
            department_id=department_id,
            location_id=location_id,
            employee_id=employee_id,
            notes=notes,
            source=source,
            purchase_date=purchase_date,
            warranty_end_date=warranty_end_date,
            price=price,
            manufacturer_id=manufacturer_id,
            supplier_id=supplier_id
        )
        
        # Ищем устройство для обновления
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        
        # Обновляем данные устройства
        for key, value in form_data.items():
            setattr(device, key, value)
            
        device.updated_at = datetime.now()
        
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Устанавливаем сообщение об успехе
        request.session["message"] = {"type": "success", "text": "Актив успешно обновлен!"}
        
        # Перенаправляем на дашборд
        return RedirectResponse(
            url=request.url_for("read_assets"),
            status_code=status.HTTP_303_SEE_OTHER
        )
        
    except Exception as e:
        db.rollback()
        # Устанавливаем сообщение об ошибке
        request.session["message"] = {"type": "danger", "text": f"Ошибка при обновлении актива: {str(e)}"}
        
        # Возвращаем обратно на форму редактирования
        return RedirectResponse(
            url=request.url_for("edit_asset", device_id=device_id),
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/delete/{device_id}", name="delete_asset")
async def delete_asset(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Обрабатывает удаление актива.
    """
    try:
        # Ищем устройство для удаления
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        
        # Удаляем устройство
        db.delete(device)
        db.commit()
        
        # Устанавливаем сообщение об успехе
        request.session["message"] = {"type": "success", "text": "Актив успешно удален!"}
        
    except Exception as e:
        db.rollback()
        # Устанавливаем сообщение об ошибке
        request.session["message"] = {"type": "danger", "text": f"Ошибка при удалении актива: {str(e)}"}
    
    # Перенаправляем на дашборд
    return RedirectResponse(
        url=request.url_for("read_assets"),
        status_code=status.HTTP_303_SEE_OTHER
    )