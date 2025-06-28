# app/api/endpoints/dictionaries.py

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.db.database import get_db
from app.models import (
    AssetType, DeviceModel, DeviceStatus, Manufacturer, 
    Department, Location, Employee
)
from app.services.audit_log_service import log_action
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация APIRouter
router = APIRouter(prefix="/api/dictionaries", tags=["dictionaries"])

# Эндпоинты для типов активов (AssetType)
@router.get("/asset-types", response_model=List[dict])
async def get_asset_types(db: Session = Depends(get_db)):
    """Получить список всех типов активов"""
    try:
        asset_types = db.query(AssetType).order_by(AssetType.name).all()
        return [{"id": t.id, "name": t.name, "description": t.description} for t in asset_types]
    except Exception as e:
        logger.error(f"Error getting asset types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении типов активов: {str(e)}")

@router.post("/asset-types", response_model=dict)
async def create_asset_type(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать новый тип актива"""
    try:
        asset_type = AssetType(name=name.strip(), description=description.strip() if description else None)
        db.add(asset_type)
        db.commit()
        db.refresh(asset_type)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="AssetType",
            entity_id=asset_type.id,
            details={"name": asset_type.name}
        )
        
        return {
            "id": asset_type.id, 
            "name": asset_type.name, 
            "description": asset_type.description,
            "message": "Тип актива успешно создан"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Тип актива с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating asset type: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании типа актива: {str(e)}"
        )

# Эндпоинты для моделей устройств (DeviceModel)
@router.get("/device-models", response_model=List[dict])
async def get_device_models(db: Session = Depends(get_db)):
    """Получить список всех моделей устройств"""
    try:
        device_models = db.query(DeviceModel).order_by(DeviceModel.name).all()
        return [
            {
                "id": m.id, 
                "name": m.name, 
                "manufacturer_id": m.manufacturer_id,
                "manufacturer_name": m.manufacturer.name if m.manufacturer else None,
                "asset_type_id": m.asset_type_id,
                "asset_type_name": m.asset_type.name if m.asset_type else None,
                "description": m.description
            } 
            for m in device_models
        ]
    except Exception as e:
        logger.error(f"Error getting device models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении моделей устройств: {str(e)}")

@router.post("/device-models", response_model=dict)
async def create_device_model(
    name: str = Form(...),
    manufacturer_id: int = Form(...),
    asset_type_id: int = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать новую модель устройства"""
    try:
        # Проверяем существование производителя и типа актива
        manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Производитель не найден")
            
        asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
        if not asset_type:
            raise HTTPException(status_code=404, detail="Тип актива не найден")
        
        device_model = DeviceModel(
            name=name.strip(), 
            manufacturer_id=manufacturer_id,
            asset_type_id=asset_type_id,
            description=description.strip() if description else None,
            specification={}
        )
        db.add(device_model)
        db.commit()
        db.refresh(device_model)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="DeviceModel",
            entity_id=device_model.id,
            details={"name": device_model.name, "manufacturer_id": device_model.manufacturer_id}
        )
        
        return {
            "id": device_model.id, 
            "name": device_model.name,
            "manufacturer_id": device_model.manufacturer_id,
            "manufacturer_name": manufacturer.name,
            "asset_type_id": device_model.asset_type_id,
            "asset_type_name": asset_type.name,
            "description": device_model.description,
            "message": "Модель устройства успешно создана"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Модель устройства с таким названием уже существует"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating device model: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании модели устройства: {str(e)}"
        )

# Эндпоинты для статусов устройств (DeviceStatus)
@router.get("/device-statuses", response_model=List[dict])
async def get_device_statuses(db: Session = Depends(get_db)):
    """Получить список всех статусов устройств"""
    try:
        device_statuses = db.query(DeviceStatus).order_by(DeviceStatus.name).all()
        return [{"id": s.id, "name": s.name, "description": s.description} for s in device_statuses]
    except Exception as e:
        logger.error(f"Error getting device statuses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статусов устройств: {str(e)}")

@router.post("/device-statuses", response_model=dict)
async def create_device_status(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать новый статус устройства"""
    try:
        device_status = DeviceStatus(name=name.strip(), description=description.strip() if description else None)
        db.add(device_status)
        db.commit()
        db.refresh(device_status)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="DeviceStatus",
            entity_id=device_status.id,
            details={"name": device_status.name}
        )
        
        return {
            "id": device_status.id, 
            "name": device_status.name, 
            "description": device_status.description,
            "message": "Статус устройства успешно создан"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Статус устройства с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating device status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании статуса устройства: {str(e)}"
        )

# Эндпоинты для производителей (Manufacturer)
@router.get("/manufacturers", response_model=List[dict])
async def get_manufacturers(db: Session = Depends(get_db)):
    """Получить список всех производителей"""
    try:
        manufacturers = db.query(Manufacturer).order_by(Manufacturer.name).all()
        return [{"id": m.id, "name": m.name, "description": m.description} for m in manufacturers]
    except Exception as e:
        logger.error(f"Error getting manufacturers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении производителей: {str(e)}")

@router.post("/manufacturers", response_model=dict)
async def create_manufacturer(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать нового производителя"""
    try:
        manufacturer = Manufacturer(name=name.strip(), description=description.strip() if description else None)
        db.add(manufacturer)
        db.commit()
        db.refresh(manufacturer)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Manufacturer",
            entity_id=manufacturer.id,
            details={"name": manufacturer.name}
        )
        
        return {
            "id": manufacturer.id, 
            "name": manufacturer.name, 
            "description": manufacturer.description,
            "message": "Производитель успешно создан"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Производитель с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating manufacturer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании производителя: {str(e)}"
        )

# Эндпоинты для отделов (Department)
@router.get("/departments", response_model=List[dict])
async def get_departments(db: Session = Depends(get_db)):
    """Получить список всех отделов"""
    try:
        departments = db.query(Department).order_by(Department.name).all()
        return [{"id": d.id, "name": d.name, "description": d.description} for d in departments]
    except Exception as e:
        logger.error(f"Error getting departments: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении отделов: {str(e)}")

@router.post("/departments", response_model=dict)
async def create_department(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать новый отдел"""
    try:
        department = Department(name=name.strip(), description=description.strip() if description else None)
        db.add(department)
        db.commit()
        db.refresh(department)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Department",
            entity_id=department.id,
            details={"name": department.name}
        )
        
        return {
            "id": department.id, 
            "name": department.name, 
            "description": department.description,
            "message": "Отдел успешно создан"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Отдел с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating department: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании отдела: {str(e)}"
        )

# Эндпоинты для местоположений (Location)
@router.get("/locations", response_model=List[dict])
async def get_locations(db: Session = Depends(get_db)):
    """Получить список всех местоположений"""
    try:
        locations = db.query(Location).order_by(Location.name).all()
        return [{"id": l.id, "name": l.name, "description": l.description} for l in locations]
    except Exception as e:
        logger.error(f"Error getting locations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении местоположений: {str(e)}")

@router.post("/locations", response_model=dict)
async def create_location(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать новое местоположение"""
    try:
        location = Location(name=name.strip(), description=description.strip() if description else None)
        db.add(location)
        db.commit()
        db.refresh(location)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Location",
            entity_id=location.id,
            details={"name": location.name}
        )
        
        return {
            "id": location.id, 
            "name": location.name, 
            "description": location.description,
            "message": "Местоположение успешно создано"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Местоположение с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating location: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании местоположения: {str(e)}"
        )

# Эндпоинты для сотрудников (Employee)
@router.get("/employees", response_model=List[dict])
async def get_employees(db: Session = Depends(get_db)):
    """Получить список всех сотрудников"""
    try:
        employees = db.query(Employee).order_by(Employee.last_name, Employee.first_name).all()
        return [
            {
                "id": e.id, 
                "first_name": e.first_name, 
                "last_name": e.last_name,
                "patronymic": e.patronymic,
                "employee_id": e.employee_id,
                "email": e.email,
                "phone_number": e.phone_number,
                "full_name": f"{e.last_name} {e.first_name} {e.patronymic or ''}"
            } 
            for e in employees
        ]
    except Exception as e:
        logger.error(f"Error getting employees: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении сотрудников: {str(e)}")

@router.post("/employees", response_model=dict)
async def create_employee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    patronymic: Optional[str] = Form(None),
    employee_id: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создать нового сотрудника"""
    try:
        employee = Employee(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            patronymic=patronymic.strip() if patronymic else None,
            employee_id=employee_id.strip() if employee_id else None,
            email=email.strip() if email else None,
            phone_number=phone_number.strip() if phone_number else None
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        # Логируем создание
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Employee",
            entity_id=employee.id,
            details={"name": f"{employee.last_name} {employee.first_name}"}
        )
        
        return {
            "id": employee.id, 
            "first_name": employee.first_name, 
            "last_name": employee.last_name,
            "patronymic": employee.patronymic,
            "employee_id": employee.employee_id,
            "email": employee.email,
            "phone_number": employee.phone_number,
            "full_name": f"{employee.last_name} {employee.first_name} {employee.patronymic or ''}",
            "message": "Сотрудник успешно создан"
        }
    except IntegrityError as e:
        db.rollback()
        if "employee_id" in str(e).lower():
            detail = "Сотрудник с таким ID уже существует"
        elif "email" in str(e).lower():
            detail = "Сотрудник с таким email уже существует"
        else:
            detail = "Ошибка уникальности данных"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating employee: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании сотрудника: {str(e)}"
        )