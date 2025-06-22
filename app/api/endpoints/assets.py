# app/api/endpoints/assets.py

from datetime import datetime, date
from typing import Optional
import io
import csv
from fastapi import APIRouter, Response, Request, HTTPException, Form, Depends, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload
from datetime import timezone
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
import psycopg2.errors
import json

from app.db.database import get_db
from app.models import (
    Device, DeviceModel, AssetType, DeviceStatus, Department, Location,
    Employee, Manufacturer, ActionLog
)
from app.services.audit_log_service import log_action # Импортируем сервис логирования
from app.flash import flash
from app.templating import templates

# Инициализация APIRouter
router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse, name="read_assets")
async def read_assets(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Количество элементов на странице"),
    search: Optional[str] = Query(None, description="Поиск по инвентарному/серийному номеру или MAC"),
    asset_type_id: Optional[str] = Query(None, description="Фильтр по типу актива (ID)"),
    status_id: Optional[str] = Query(None, description="Фильтр по статусу (ID)"),
    department_id: Optional[str] = Query(None, description="Фильтр по отделу (ID)"),
    location_id: Optional[str] = Query(None, description="Фильтр по локации (ID)"),
    manufacturer_id: Optional[str] = Query(None, description="Фильтр по производителю (ID)"),
):
    """Отображает дашборд со списком активов и статистикой."""
    try:
        def safe_int(value: Optional[str]) -> Optional[int]:
            """Безопасно преобразует строку в int, игнорируя пустые строки и None."""
            if value is None or value == "":
                return None
            return int(value)

        # Преобразуем строковые ID из фильтров в целые числа
        asset_type_id_int = safe_int(asset_type_id)
        status_id_int = safe_int(status_id)
        department_id_int = safe_int(department_id)
        location_id_int = safe_int(location_id)
        manufacturer_id_int = safe_int(manufacturer_id)

        offset = (page - 1) * page_size
        
        # Получаем список устройств с жадной загрузкой связанных данных
        query = db.query(Device).options(
            joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
            joinedload(Device.asset_type),
            joinedload(Device.status),
            joinedload(Device.department),
            joinedload(Device.location),
            joinedload(Device.employee)
        )
        
        # Применяем фильтры
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Device.inventory_number.ilike(search_term)) |
                (Device.serial_number.ilike(search_term)) |
                (Device.mac_address.ilike(search_term))
            )
        if asset_type_id_int: query = query.filter(Device.asset_type_id == asset_type_id_int)
        if status_id_int: query = query.filter(Device.status_id == status_id_int)
        if department_id_int: query = query.filter(Device.department_id == department_id_int)
        if location_id_int: query = query.filter(Device.location_id == location_id_int)
        if manufacturer_id_int: query = query.join(Device.device_model).filter(DeviceModel.manufacturer_id == manufacturer_id_int)
        
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

        # Сортируем и получаем общее количество после фильтрации
        query = query.order_by(Device.updated_at.desc())
        total_devices = query.count()
        
        # Применяем пагинацию
        paginated_devices = query.offset(offset).limit(page_size).all()
        
        # Данные для выпадающих списков в фильтрах
        asset_types = db.query(AssetType).order_by(AssetType.name).all()
        device_statuses = db.query(DeviceStatus).order_by(DeviceStatus.name).all()
        departments = db.query(Department).order_by(Department.name).all()
        locations = db.query(Location).order_by(Location.name).all()
        manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
        
        # Собираем фильтры в словарь для заполнения полей формы
        filters = {
            "search": search,
            "asset_type_id": asset_type_id_int,
            "status_id": status_id_int,
            "department_id": department_id_int,
            "location_id": location_id_int,
            "manufacturer_id": manufacturer_id_int,
            "page_size": page_size,
        }

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
            "title": "IT Asset Tracker - Дашборд",
            "asset_types": asset_types,
            "device_statuses": device_statuses,
            "departments": departments,
            "locations": locations,
            "manufacturers": manufacturers,
            "filters": filters,
            "query_params": {k: v for k, v in filters.items() if v is not None},
        }
        
        print(f"Template context: {context}")
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        print(f"Error in read_assets: {str(e)}")
        # Возвращаем страницу с ошибкой.
        error_text = f"Ошибка при загрузке данных: {str(e)}"
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": error_text,
                "page": 1, # Значения по умолчанию для пагинации
                "page_size": 20,
                "device_types_count": [],
                "device_statuses_count": [],
                "total_pages": 1,
                "message": {"type": "danger", "text": error_text},
                "title": "Ошибка - IT Asset Tracker",
            },
            status_code=500
        )

@router.get("/export/csv", name="export_assets_csv")
async def export_assets_csv(
    request: Request,
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Поиск по инвентарному/серийному номеру или MAC"),
    asset_type_id: Optional[str] = Query(None, description="Фильтр по типу актива (ID)"),
    status_id: Optional[str] = Query(None, description="Фильтр по статусу (ID)"),
    department_id: Optional[str] = Query(None, description="Фильтр по отделу (ID)"),
    location_id: Optional[str] = Query(None, description="Фильтр по локации (ID)"),
    manufacturer_id: Optional[str] = Query(None, description="Фильтр по производителю (ID)"),
):
    """Экспортирует отфильтрованный список активов в CSV файл."""
    try:
        def safe_int(value: Optional[str]) -> Optional[int]:
            """Безопасно преобразует строку в int, игнорируя пустые строки и None."""
            if value is None or value == "":
                return None
            return int(value)

        asset_type_id_int = safe_int(asset_type_id)
        status_id_int = safe_int(status_id)
        department_id_int = safe_int(department_id)
        location_id_int = safe_int(location_id)
        manufacturer_id_int = safe_int(manufacturer_id)

        query = db.query(Device).options(
            joinedload(Device.device_model).joinedload(DeviceModel.manufacturer),
            joinedload(Device.asset_type),
            joinedload(Device.status),
            joinedload(Device.department),
            joinedload(Device.location),
            joinedload(Device.employee)
        )

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Device.inventory_number.ilike(search_term)) |
                (Device.serial_number.ilike(search_term)) |
                (Device.mac_address.ilike(search_term))
            )
        if asset_type_id_int: query = query.filter(Device.asset_type_id == asset_type_id_int)
        if status_id_int: query = query.filter(Device.status_id == status_id_int)
        if department_id_int: query = query.filter(Device.department_id == department_id_int)
        if location_id_int: query = query.filter(Device.location_id == location_id_int)
        if manufacturer_id_int: query = query.join(Device.device_model).filter(DeviceModel.manufacturer_id == manufacturer_id_int)

        devices = query.order_by(Device.id).all()

        output = io.StringIO()
        output.write('\ufeff')  # BOM для корректного отображения кириллицы в Excel
        writer = csv.writer(output)

        headers = [
            "ID", "Инвентарный номер", "Серийный номер", "MAC-адрес", "IP-адрес",
            "Тип", "Производитель", "Модель", "Статус", "Отдел", "Локация",
            "Сотрудник", "Дата покупки", "Окончание гарантии", "Цена", "Заметки",
            "Дата создания", "Дата обновления"
        ]
        writer.writerow(headers)

        for device in devices:
            employee_name = f"{device.employee.last_name} {device.employee.first_name}" if device.employee else ""
            row = [
                device.id, device.inventory_number, device.serial_number, device.mac_address, device.ip_address,
                device.asset_type.name if device.asset_type else "",
                device.device_model.manufacturer.name if device.device_model and device.device_model.manufacturer else "",
                device.device_model.name if device.device_model else "",
                device.status.name if device.status else "",
                device.department.name if device.department else "",
                device.location.name if device.location else "",
                employee_name, device.purchase_date, device.warranty_end_date, device.price, device.notes,
                device.created_at.strftime("%Y-%m-%d %H:%M:%S") if device.created_at else "",
                device.updated_at.strftime("%Y-%m-%d %H:%M:%S") if device.updated_at else "",
            ]
            writer.writerow(row)

        output.seek(0)
        filename = f"assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response_headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
        return StreamingResponse(io.StringIO(output.getvalue()), media_type="text/csv", headers=response_headers)

    except Exception as e:
        print(f"Error exporting to CSV: {str(e)}")
        request.session["message"] = {"type": "danger", "text": f"Ошибка при экспорте в CSV: {str(e)}"}
        return RedirectResponse(url=request.url_for("read_assets"), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/add", response_class=HTMLResponse, name="add_asset_form")
async def add_asset_form(request: Request, db: Session = Depends(get_db), error: str = None):
    """
    Отображает форму для добавления нового актива.
    """
    # Создаем пустой объект device для рендеринга формы
    # Используем простой словарь для инициализации полей формы
    device = {
        'id': None, 'inventory_number': '', 'serial_number': '', 'mac_address': '',
        'ip_address': '', 'asset_type_id': None, 'device_model_id': None,
        'status_id': None, 'department_id': None, 'location_id': None,
        'employee_id': None, 'notes': '', 'source': 'purchase', 'purchase_date': None,
        'warranty_end_date': None, 'price': None, 'expected_lifespan_years': None,
        'current_wear_percentage': None
    }
    
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

        )
        
        db.add(device)
        try:
            db.commit()
            db.refresh(device)
        except IntegrityError:
            db.rollback()
            flash(request, "Актив с таким инвентарным номером уже существует!", "danger")
            return RedirectResponse(url=request.url_for("add_asset_form"), status_code=status.HTTP_303_SEE_OTHER)
        
        # Логируем создание устройства
        log_action(
            db=db,
            user_id=1, # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Device",
            entity_id=device.id,
            details={"inventory_number": device.inventory_number, "device_model_id": device.device_model_id}
        )
        # Устанавливаем сообщение об успехе в сессию
        flash(request, "Актив успешно добавлен!", "success")
        # Перенаправляем на страницу списка активов
        return RedirectResponse(url=request.url_for("read_assets"), status_code=status.HTTP_303_SEE_OTHER)
        
    except IntegrityError as e:
        db.rollback()
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            error_msg = "Актив с таким инвентарным номером уже существует!"
        else:
            error_msg = f"Ошибка базы данных при создании актива: {e.orig}"
        print(f"Error creating asset: {error_msg}")
        
        # Устанавливаем сообщение об ошибке в сессию
        flash(request, error_msg, "danger")
        # Перенаправляем обратно на форму добавления
        return RedirectResponse(
            url=request.url_for("add_asset_form"), 
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        db.rollback()
        error_msg = f"Непредвиденная ошибка при создании актива: {str(e)}"
        print(f"Unexpected error creating asset: {error_msg}")
        flash(request, error_msg, "danger")
        return RedirectResponse(
            url=request.url_for("add_asset_form"),
            status_code=status.HTTP_303_SEE_OTHER
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

        # Собираем данные из формы для логирования
        update_data = {
            "inventory_number": inventory_number,
            "serial_number": serial_number,
            "mac_address": mac_address,
            "ip_address": ip_address,
            "asset_type_id": asset_type_id,
            "device_model_id": device_model_id,
            "status_id": status_id,
            "department_id": department_id,
            "location_id": location_id,
            "employee_id": employee_id,
            "notes": notes,
            "source": source,
            "purchase_date": purchase_date,
            "warranty_end_date": warranty_end_date,
            "price": price,
            "expected_lifespan_years": expected_lifespan_years,
            "current_wear_percentage": current_wear_percentage,
        }
        
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
        # updated_at будет обновлено автоматически благодаря onupdate=func.now()
        
        # Сохраняем изменения
        db.commit()
        db.refresh(device)
        
        # Логируем обновление устройства
        log_action(
            db=db,
            user_id=None, # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="Device",
            entity_id=device.id,
            details={"updated_fields": {k: v for k, v in update_data.items() if v is not None}}
        )
        flash(request, "Актив успешно обновлен!", "success")
        # Перенаправляем на страницу списка активов с сообщением об успехе
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        return response
        
    except IntegrityError as e:
        db.rollback()
        if isinstance(e.orig, psycopg2.errors.UniqueViolation):
            error_msg = "Актив с таким инвентарным номером уже существует!"
            flash(request, error_msg, "danger")
            return RedirectResponse(
                url=request.url_for("edit_asset", device_id=device_id),
                status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            error_msg = f"Ошибка при обновлении актива: {str(e)}"
            print(f"Error updating asset: {error_msg}")
            flash(request, error_msg, "danger")
            return RedirectResponse(
                url=request.url_for("edit_asset", device_id=device_id),
                status_code=status.HTTP_303_SEE_OTHER
            )
    except Exception as e:
        db.rollback()
        error_msg = f"Непредвиденная ошибка при обновлении актива: {str(e)}"
        print(f"Unexpected error updating asset: {error_msg}")
        flash(request, error_msg, "danger")
        return RedirectResponse(
            url=request.url_for("edit_asset", device_id=device_id),
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.post("/delete/{device_id}", name="delete_asset") # Метод POST для форм
async def delete_asset(device_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Обрабатывает удаление актива.
    """
    try:
        # Получаем устройство по ID
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            flash(request, "Устройство не найдено.", "danger")
            return RedirectResponse(url=request.url_for("read_assets"), status_code=status.HTTP_303_SEE_OTHER)
    
        # Сохраняем данные перед удалением для лога
        device_data = {
            "inventory_number": device.inventory_number,
            "device_model_id": device.device_model_id,
        }
        
        # Логируем удаление
        log_action(
            db=db,
            user_id=1, # TODO: Заменить на ID аутентифицированного пользователя
            action_type="delete",
            entity_type="Device",
            entity_id=device.id,
            details=device_data
        )

        db.delete(device)
        db.commit()
        flash(request, "Актив успешно удален.", "success")
        return RedirectResponse(url=request.url_for("read_assets"), status_code=status.HTTP_303_SEE_OTHER)
    
    except Exception as e:
        db.rollback()
        # import logging
        # logging.error(f"Ошибка при удалении устройства ID {device_id}", exc_info=True)
        print(f"Ошибка при удалении устройства: {e}")
        flash(request, f"Ошибка при удалении актива: {str(e)}", "danger")
        return RedirectResponse(url=request.url_for("read_assets"), status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logs", response_class=HTMLResponse, name="view_logs")
async def view_logs(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Отображает страницу с логами действий с возможностью фильтрации
    """
    try:
        query = db.query(ActionLog)
        
        # Применяем фильтры
        if user_id is not None:
            query = query.filter(ActionLog.user_id == user_id)
        if action_type:
            query = query.filter(ActionLog.action_type == action_type)
        if entity_type:
            query = query.filter(ActionLog.entity_type == entity_type)
        if entity_id is not None:
            query = query.filter(ActionLog.entity_id == entity_id)
        if start_date:
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            query = query.filter(ActionLog.timestamp >= start_date)
        if end_date:
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)
            end_date = end_date.replace(hour=23, minute=59, second=59)
            query = query.filter(ActionLog.timestamp <= end_date)
        
        logs = query.order_by(ActionLog.timestamp.desc()).offset(skip).limit(limit).all()
        
        action_types = db.query(ActionLog.action_type).distinct().all()
        entity_types = db.query(ActionLog.entity_type).distinct().all()
        
        filters = {
            "user_id": user_id, "action_type": action_type, "entity_type": entity_type,
            "entity_id": entity_id, "start_date": start_date.date() if start_date else None,
            "end_date": end_date.date() if end_date else None,
        }
        
        return templates.TemplateResponse(
            "audit_logs.html",
            {
                "request": request, "logs": logs, "action_types": [t[0] for t in action_types if t[0]],
                "entity_types": [t[0] for t in entity_types if t[0]], "filters": filters,
                "title": "Журнал действий"
            }
        )
        
    except Exception as e:
        print(f"Ошибка при получении логов: {str(e)}")
        flash(request, f"Произошла ошибка при загрузке логов: {str(e)}", "danger")
        return RedirectResponse(url=request.url_for("read_assets"), status_code=status.HTTP_303_SEE_OTHER)
