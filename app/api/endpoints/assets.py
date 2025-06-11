# app/api/endpoints/assets.py

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Response, Request, HTTPException, Form, Depends, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
import psycopg2.errors
import json

from app.db.database import get_db
from app.models import (
    Device, DeviceModel, AssetType, DeviceStatus, 
    Department, Location, Employee, Manufacturer
)
from app.config import TEMPLATES_DIR

# Инициализация Jinja2Templates с настройками для корректного отображения кириллицы
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Добавляем пользовательский фильтр для форматирования JSON с кириллицей
def to_pretty_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2)

templates.env.filters['to_pretty_json'] = to_pretty_json

# Инициализация APIRouter
router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse, name="read_assets")
async def read_assets(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Количество элементов на странице"),
):
    """Отображает дашборд со списком активов и статистикой."""
    try:
        offset = (page - 1) * page_size
        
        # Получаем список устройств с жадной загрузкой связанных данных
        devices = db.query(Device).options(
            joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
            joinedload(Device.asset_type),
            joinedload(Device.status),
            joinedload(Device.department),
            joinedload(Device.location),
            joinedload(Device.employee)
        ).order_by(Device.updated_at.desc())
        
        # Применяем пагинацию
        paginated_devices = devices.offset(offset).limit(page_size).all()
        total_devices = devices.count()
        
        # Получаем статистику по типам устройств
        device_types_count = db.query(
            AssetType.name,
            func.count(Device.id).label('count')
        ).join(
            Device, Device.asset_type_id == AssetType.id
        ).group_by(
            AssetType.name
        ).all()

        # Получаем статистику по статусам устройств
        device_statuses_count = db.query(
            DeviceStatus.name,
            func.count(Device.id).label('count')
        ).join(
            Device, Device.status_id == DeviceStatus.id
        ).group_by(
            DeviceStatus.name
        ).all()
        
        # Преобразуем результаты запросов в списки словарей
        device_types_list = [{"name": name, "count": count} for name, count in device_types_count]
        device_statuses_list = [{"name": name, "count": count} for name, count in device_statuses_count]
        
        # Логируем результаты для отладки
        print(f"Device types count: {device_types_list}")
        print(f"Device statuses count: {device_statuses_list}")

        # Собираем контекст для шаблона
        context = {
            "request": request,  # Важно передать request для работы url_for
            "devices": paginated_devices,
            "total_devices": total_devices,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_devices + page_size - 1) // page_size if page_size > 0 else 1,
            "device_types_count": device_types_list,
            "device_statuses_count": device_statuses_list,
            "title": "IT Asset Tracker - Дашборд"
        }
        
        print(f"Template context: {context}")
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        print(f"Error in read_assets: {str(e)}")
        # Возвращаем ошибку с описанием
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": f"Ошибка при загрузке данных: {str(e)}",
                "title": "Ошибка",
                "page": 1,
                "page_size": page_size,
                "device_types_count": [],
                "device_statuses_count": [],
                "total_pages": 1,
                "message": {"type": "danger", "text": f"Ошибка при загрузке данных: {str(e)}"},
                "title": "Ошибка - IT Asset Tracker"
            },
            status_code=500
        )

@router.get("/add", response_class=HTMLResponse, name="add_asset_form")
async def add_asset_form(request: Request, db: Session = Depends(get_db), error: str = None):
    """
    Отображает форму для добавления нового актива.
    """
    # Создаем пустой объект device для рендеринга формы
    device = type('Device', (object,), {
        'id': None, 'inventory_number': '', 'serial_number': '',
        'mac_address': '', 'ip_address': '', 'asset_type_id': None,
        'device_model_id': None, 'status_id': None, 'department_id': None,
        'location_id': None, 'employee_id': None, 'notes': '', 'source': 'purchase',
        'purchase_date': None, 'warranty_end_date': None, 'price': None,
        'expected_lifespan_years': None, 'current_wear_percentage': None
    })()
    
    # Получаем сообщение об ошибке из параметра запроса, если оно есть
    error_message = request.query_params.get('error') if not error else error

    try:
        # Загружаем данные для выпадающих списков из базы данных
        asset_types = db.query(AssetType).order_by(AssetType.name).all()
        device_models = db.query(DeviceModel).order_by(DeviceModel.name).all()
        device_statuses = db.query(DeviceStatus).order_by(DeviceStatus.name).all()
        departments = db.query(Department).order_by(Department.name).all()
        locations = db.query(Location).order_by(Location.name).all()
        employees = db.query(Employee).order_by(Employee.last_name, Employee.first_name).all()

        return templates.TemplateResponse(
            "add_asset.html",
            {
                "request": request,
                "device": device,
                "asset_types": asset_types,
                "device_models": device_models,
                "device_statuses": device_statuses,
                "departments": departments,
                "locations": locations,
                "employees": employees,
                "error": error_message,
                "title": "Добавить актив"
            }
        )
    except Exception as e:
        print(f"Error loading form data: {e}")
        return templates.TemplateResponse(
            "add_asset.html",
            {
                "request": request,
                "error": f"Ошибка при загрузке данных: {str(e)}",
                "title": "Ошибка"
            }
        )

@router.post("/create", response_class=HTMLResponse, name="create_asset")
async def create_asset(
    request: Request,
    inventory_number: str = Form(...),
    serial_number: str = Form(""),
    mac_address: str = Form(""),
    ip_address: str = Form(""),
    asset_type_id: str = Form(...),
    device_model_id: str = Form(...),
    status_id: str = Form(...),
    department_id: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    employee_id: Optional[str] = Form(None),
    notes: str = Form(""),
    source: str = Form("purchase"),
    purchase_date: Optional[str] = Form(None),
    warranty_end_date: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    expected_lifespan_years: Optional[str] = Form(None),
    current_wear_percentage: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Обрабатывает отправку формы создания нового актива.
    """
    try:
        # Функция для безопасного преобразования в int
        def safe_int(value):
            if value and str(value).strip():
                return int(value)
            return None
        
        # Функция для безопасного преобразования в float
        def safe_float(value):
            if value and str(value).strip():
                return float(value)
            return None
        
        # Функция для безопасного парсинга даты
        def safe_date(value):
            if value and str(value).strip():
                try:
                    return datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None
        
        # Создаем новый объект Device
        device = Device(
            inventory_number=inventory_number.strip(),
            serial_number=serial_number.strip() if serial_number else None,
            mac_address=mac_address.strip() if mac_address else None,
            ip_address=ip_address.strip() if ip_address else None,
            asset_type_id=int(asset_type_id),
            device_model_id=int(device_model_id),
            status_id=int(status_id),
            department_id=safe_int(department_id),
            location_id=safe_int(location_id),
            employee_id=safe_int(employee_id),
            notes=notes.strip() if notes else None,
            source=source,
            purchase_date=safe_date(purchase_date),
            warranty_end_date=safe_date(warranty_end_date),
            price=safe_float(price),
            expected_lifespan_years=safe_int(expected_lifespan_years),
            current_wear_percentage=safe_int(current_wear_percentage),
            added_at=datetime.utcnow()
        )
        
        # Добавляем в сессию и сохраняем
        db.add(device)
        db.commit()
        db.refresh(device)
        
        # Перенаправляем на страницу списка активов с сообщением об успехе
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        return response
        
    except IntegrityError as e:
        db.rollback()
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            error_msg = "Актив с таким инвентарным номером уже существует!"
        else:
            error_msg = f"Ошибка при создании актива: {str(e)}"
        print(f"Error creating asset: {error_msg}")
        # В случае ошибки возвращаем ту же форму с сообщением об ошибке
        return await add_asset_form(
            request=request,
            db=db,
            error=error_msg
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error creating asset: {e}")
        # В случае ошибки возвращаем ту же форму с сообщением об ошибке
        return await add_asset_form(
            request=request,
            db=db,
            error=f"Непредвиденная ошибка при создании актива: {str(e)}"
        )

@router.get("/edit/{device_id}", response_class=HTMLResponse, name="edit_asset")
async def edit_asset(request: Request, device_id: int, db: Session = Depends(get_db)):
    """
    Отображает форму для редактирования существующего актива.
    """
    try:
        # Получаем устройство по ID
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
            
        # Загружаем данные для выпадающих списков
        asset_types = db.query(AssetType).order_by(AssetType.name).all()
        device_models = db.query(DeviceModel).order_by(DeviceModel.name).all()
        device_statuses = db.query(DeviceStatus).order_by(DeviceStatus.name).all()
        departments = db.query(Department).order_by(Department.name).all()
        locations = db.query(Location).order_by(Location.name).all()
        employees = db.query(Employee).order_by(Employee.last_name, Employee.first_name).all()
        
        return templates.TemplateResponse(
            "edit_asset.html",
            {
                "request": request,
                "device": device,
                "asset_types": asset_types,
                "device_models": device_models,
                "device_statuses": device_statuses,
                "departments": departments,
                "locations": locations,
                "employees": employees,
                "title": f"Редактировать актив #{device.id}"
            }
        )
        
    except Exception as e:
        print(f"Error loading edit form: {e}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": f"Ошибка при загрузке формы редактирования: {str(e)}",
                "title": "Ошибка"
            },
            status_code=500
        )

@router.post("/update/{device_id}", response_class=HTMLResponse, name="update_asset")
async def update_asset(
    request: Request,
    device_id: int,
    inventory_number: str = Form(...),
    serial_number: str = Form(""),
    mac_address: str = Form(""),
    ip_address: str = Form(""),
    asset_type_id: str = Form(...),
    device_model_id: str = Form(...),
    status_id: str = Form(...),
    department_id: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    employee_id: Optional[str] = Form(None),
    notes: str = Form(""),
    source: str = Form("purchase"),
    purchase_date: Optional[str] = Form(None),
    warranty_end_date: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    expected_lifespan_years: Optional[str] = Form(None),
    current_wear_percentage: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Обрабатывает обновление существующего актива.
    """
    try:
        # Получаем устройство по ID
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")
        
        # Функция для безопасного преобразования в int
        def safe_int(value):
            if value and str(value).strip():
                return int(value)
            return None
        
        # Функция для безопасного преобразования в float
        def safe_float(value):
            if value and str(value).strip():
                return float(value)
            return None
        
        # Функция для безопасного парсинга даты
        def safe_date(value):
            if value and str(value).strip():
                try:
                    return datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None
        
        # Обновляем данные устройства с безопасной обработкой значений
        device.inventory_number = inventory_number.strip()
        device.serial_number = serial_number.strip() if serial_number else None
        device.mac_address = mac_address.strip() if mac_address else None
        device.ip_address = ip_address.strip() if ip_address else None
        device.asset_type_id = int(asset_type_id)
        device.device_model_id = int(device_model_id)
        device.status_id = int(status_id)
        device.department_id = safe_int(department_id)
        device.location_id = safe_int(location_id)
        device.employee_id = safe_int(employee_id)
        device.notes = notes.strip() if notes else None
        device.source = source
        device.purchase_date = safe_date(purchase_date)
        device.warranty_end_date = safe_date(warranty_end_date)
        device.price = safe_float(price)
        device.expected_lifespan_years = safe_int(expected_lifespan_years)
        device.current_wear_percentage = safe_int(current_wear_percentage)
        device.updated_at = datetime.utcnow()
        
        # Сохраняем изменения
        db.commit()
        db.refresh(device)
        
        # Перенаправляем на страницу списка активов с сообщением об успехе
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        return response
        
    except IntegrityError as e:
        db.rollback()
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            error_msg = "Актив с таким инвентарным номером уже существует!"
            request.session["message"] = {"type": "danger", "text": error_msg}
            return RedirectResponse(
                url=request.url_for("edit_asset", device_id=device_id),
                status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            error_msg = f"Ошибка при обновлении актива: {str(e)}"
            print(f"Error updating asset: {error_msg}")
            request.session["message"] = {"type": "danger", "text": error_msg}
            return RedirectResponse(
                url=request.url_for("edit_asset", device_id=device_id),
                status_code=status.HTTP_303_SEE_OTHER
            )
    except Exception as e:
        db.rollback()
        error_msg = f"Непредвиденная ошибка при обновлении актива: {str(e)}"
        print(f"Unexpected error updating asset: {error_msg}")
        request.session["message"] = {"type": "danger", "text": error_msg}
        return RedirectResponse(
            url=request.url_for("edit_asset", device_id=device_id),
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/delete/{device_id}", name="delete_asset")
async def delete_asset(device_id: int, db: Session = Depends(get_db)):
    """
    Обрабатывает удаление актива.
    """
    try:
        # Получаем устройство по ID
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Устройство не найдено")

        # Удаляем устройство
        db.delete(device)
        db.commit()

        return {"message": "Актив успешно удален"}

    except Exception as e:
        db.rollback()
        print(f"Ошибка при удалении устройства: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении актива: {str(e)}")
