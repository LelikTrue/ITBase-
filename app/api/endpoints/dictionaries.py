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
from app.services.action_log_service import log_action
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация APIRouter
router = APIRouter(tags=["dictionaries"])

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

@router.get("/asset-types/{asset_type_id}", response_model=dict)
async def get_asset_type(asset_type_id: int, db: Session = Depends(get_db)):
    """Получить один тип актива по ID"""
    asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
    if not asset_type:
        raise HTTPException(status_code=404, detail="Тип актива не найден")
    
    return {
        "id": asset_type.id,
        "name": asset_type.name,
        "description": asset_type.description
    }

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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="AssetType",
            entity_id=asset_type.id,
            details={
                "diff": {
                    "name": {"old": None, "new": asset_type.name},
                    "description": {"old": None, "new": asset_type.description}
                }
            }
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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="DeviceModel",
            entity_id=device_model.id,
            details={
                "diff": {
                    "name": {"old": None, "new": device_model.name},
                    "manufacturer_id": {"old": None, "new": device_model.manufacturer_id},
                    "asset_type_id": {"old": None, "new": device_model.asset_type_id},
                    "description": {"old": None, "new": device_model.description}
                }
            }
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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="DeviceStatus",
            entity_id=device_status.id,
            details={
                "diff": {
                    "name": {"old": None, "new": device_status.name},
                    "description": {"old": None, "new": device_status.description}
                }
            }
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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Manufacturer",
            entity_id=manufacturer.id,
            details={
                "diff": {
                    "name": {"old": None, "new": manufacturer.name},
                    "description": {"old": None, "new": manufacturer.description}
                }
            }
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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Department",
            entity_id=department.id,
            details={
                "diff": {
                    "name": {"old": None, "new": department.name},
                    "description": {"old": None, "new": department.description}
                }
            }
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

@router.put("/departments/{department_id}", response_model=dict)
async def update_department(
    department_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновить отдел"""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Отдел не найден")
        
        # Сохраняем старые значения
        old_name = department.name
        old_description = department.description
        
        # Обновляем значения
        department.name = name.strip()
        department.description = description.strip() if description else None
        
        db.commit()
        db.refresh(department)
        
        # Логируем изменение в едином формате
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="Department",
            entity_id=department.id,
            details={
                "diff": {
                    "name": {
                        "old": old_name,
                        "new": department.name
                    },
                    "description": {
                        "old": old_description,
                        "new": department.description
                    }
                }
            }
        )
        
        return {
            "id": department.id,
            "name": department.name,
            "description": department.description,
            "message": "Отдел успешно обновлен"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Отдел с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating department: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении отдела: {str(e)}"
        )

@router.delete("/departments/{department_id}")
async def delete_department(department_id: int, db: Session = Depends(get_db)):
    """Удалить отдел"""
    try:
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Отдел не найден")
        
        # Проверяем, используется ли отдел
        from app.models import Device
        devices_count = db.query(Device).filter(Device.department_id == department_id).count()
        
        if devices_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить отдел. Используется в {devices_count} устройствах"
            )
        
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="Department",
            entity_id=department.id,
            details={"name": department.name}
        )
        
        db.delete(department)
        db.commit()
        
        return {"message": "Отдел успешно удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении отдела: {str(e)}")

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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Location",
            entity_id=location.id,
            details={
                "diff": {
                    "name": {"old": None, "new": location.name},
                    "description": {"old": None, "new": location.description}
                }
            }
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

@router.put("/locations/{location_id}", response_model=dict)
async def update_location(
    location_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновить местоположение"""
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")
        
        # Сохраняем старые значения
        old_name = location.name
        old_description = location.description
        
        # Обновляем значения
        location.name = name.strip()
        location.description = description.strip() if description else None
        
        db.commit()
        db.refresh(location)
        
        # Логируем изменение в едином формате
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="Location",
            entity_id=location.id,
            details={
                "diff": {
                    "name": {
                        "old": old_name,
                        "new": location.name
                    },
                    "description": {
                        "old": old_description,
                        "new": location.description
                    }
                }
            }
        )
        
        return {
            "id": location.id,
            "name": location.name,
            "description": location.description,
            "message": "Местоположение успешно обновлено"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Местоположение с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating location: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении местоположения: {str(e)}"
        )

@router.delete("/locations/{location_id}")
async def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Удалить местоположение"""
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Местоположение не найдено")
        
        # Проверяем, используется ли местоположение
        from app.models import Device
        devices_count = db.query(Device).filter(Device.location_id == location_id).count()
        
        if devices_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить местоположение. Используется в {devices_count} устройствах"
            )
        
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="Location",
            entity_id=location.id,
            details={"name": location.name}
        )
        
        db.delete(location)
        db.commit()
        
        return {"message": "Местоположение успешно удалено"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении местоположения: {str(e)}")

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
        
        # Логируем создание с унифицированным форматом данных
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="create",
            entity_type="Employee",
            entity_id=employee.id,
            details={
                "diff": {
                    "last_name": {"old": None, "new": employee.last_name},
                    "first_name": {"old": None, "new": employee.first_name},
                    "patronymic": {"old": None, "new": employee.patronymic},
                    "employee_id": {"old": None, "new": employee.employee_id},
                    "email": {"old": None, "new": employee.email},
                    "phone_number": {"old": None, "new": employee.phone_number}
                }
            }
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

@router.put("/employees/{employee_id_path}", response_model=dict)
async def update_employee(
    employee_id_path: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    patronymic: Optional[str] = Form(None),
    employee_id: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновить сотрудника"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id_path).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        
        # Сохраняем старые значения
        old_first_name = employee.first_name
        old_last_name = employee.last_name
        old_patronymic = employee.patronymic
        old_employee_id = employee.employee_id
        old_email = employee.email
        old_phone_number = employee.phone_number
        
        # Обновляем значения
        employee.first_name = first_name.strip()
        employee.last_name = last_name.strip()
        employee.patronymic = patronymic.strip() if patronymic else None
        employee.employee_id = employee_id.strip() if employee_id else None
        employee.email = email.strip() if email else None
        employee.phone_number = phone_number.strip() if phone_number else None
        
        db.commit()
        db.refresh(employee)
        
        # Логируем изменение в едином формате
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="Employee",
            entity_id=employee.id,
            details={
                "diff": {
                    "first_name": {
                        "old": old_first_name,
                        "new": employee.first_name
                    },
                    "last_name": {
                        "old": old_last_name,
                        "new": employee.last_name
                    },
                    "patronymic": {
                        "old": old_patronymic,
                        "new": employee.patronymic
                    },
                    "employee_id": {
                        "old": old_employee_id,
                        "new": employee.employee_id
                    },
                    "email": {
                        "old": old_email,
                        "new": employee.email
                    },
                    "phone_number": {
                        "old": old_phone_number,
                        "new": employee.phone_number
                    }
                }
            }
        )
        
        return {
            "id": employee.id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "patronymic": employee.patronymic,
            "employee_id": employee.employee_id,
            "email": employee.email,
            "phone_number": employee.phone_number,
            "full_name": f"{employee.last_name} {employee.first_name} {employee.patronymic or ''}".strip(),
            "message": "Сотрудник успешно обновлен"
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
        logger.error(f"Error updating employee: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении сотрудника: {str(e)}"
        )

@router.delete("/employees/{employee_id}")
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Удалить сотрудника"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")

        # Проверяем, используется ли сотрудник
        from app.models import Device
        devices_count = db.query(Device).filter(Device.employee_id == employee_id).count()

        if devices_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить сотрудника. Закреплен за {devices_count} устройствами"
            )

        # Логируем удаление
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="Employee",
            entity_id=employee.id,
            details={"name": f"{employee.last_name} {employee.first_name}"}
        )

        db.delete(employee)
        db.commit()

        return {"message": "Сотрудник успешно удален"}

    except HTTPException:
        # Перебрасываем HTTP исключения, чтобы не маскировать их как 500
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting employee: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении сотрудника: {str(e)}"
        )


    """Удалить тип актива"""
    try:
        asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
        if not asset_type:
            raise HTTPException(status_code=404, detail="Тип актива не найден")
        
        # Проверяем, используется ли тип актива
        from app.models import Device
        devices_count = db.query(Device).filter(Device.asset_type_id == asset_type_id).count()
        models_count = db.query(DeviceModel).filter(DeviceModel.asset_type_id == asset_type_id).count()
        
        if devices_count > 0 or models_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить тип актива. Используется в {devices_count} устройствах и {models_count} моделях"
            )
        
        # Логируем удаление
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="AssetType",
            entity_id=asset_type.id,
            details={"name": asset_type.name}
        )
        
        db.delete(asset_type)
        db.commit()
        
        return {"message": "Тип актива успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting asset type: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении типа актива: {str(e)}"
        )

# Аналогичные эндпоинты для статусов устройств
@router.put("/device-statuses/{status_id}", response_model=dict)
async def update_device_status(
    status_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновить статус устройства"""
    try:
        status_ = db.query(DeviceStatus).filter(DeviceStatus.id == status_id).first()
        if not status_:
            raise HTTPException(status_code=404, detail="Статус устройства не найден")
        
        # Сохраняем старые значения
        old_name = status_.name
        old_description = status_.description
        
        # Обновляем значения
        status_.name = name.strip()
        status_.description = description.strip() if description else None
        
        db.commit()
        db.refresh(status_)
        
        # Логируем изменение в едином формате
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="DeviceStatus",
            entity_id=status_.id,
            details={
                "diff": {
                    "name": {
                        "old": old_name,
                        "new": status_.name
                    },
                    "description": {
                        "old": old_description,
                        "new": status_.description
                    }
                }
            }
        )
        
        return {
            "id": status_.id,
            "name": status_.name,
            "description": status_.description,
            "message": "Статус устройства успешно обновлен"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Статус устройства с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating device status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении статуса устройства: {str(e)}"
        )

@router.delete("/device-statuses/{status_id}")
async def delete_device_status(status_id: int, db: Session = Depends(get_db)):
    """Удалить статус устройства"""
    try:
        device_status = db.query(DeviceStatus).filter(DeviceStatus.id == status_id).first()
        if not device_status:
            raise HTTPException(status_code=404, detail="Статус устройства не найден")
        
        # Проверяем, использует��я ли статус
        from app.models import Device
        devices_count = db.query(Device).filter(Device.status_id == status_id).count()
        
        if devices_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить статус. Используется в {devices_count} устройствах"
            )
        
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="DeviceStatus",
            entity_id=device_status.id,
            details={"name": device_status.name}
        )
        
        db.delete(device_status)
        db.commit()
        
        return {"message": "Статус устройства успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting device status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении статуса устройства: {str(e)}"
        )

# Эндпоинты для производителей
@router.put("/manufacturers/{manufacturer_id}", response_model=dict)
async def update_manufacturer(
    manufacturer_id: int,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновить производителя"""
    try:
        manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Производитель не найден")
        
        # Сохраняем старые значения
        old_name = manufacturer.name
        old_description = manufacturer.description
        
        # Обновляем значения
        manufacturer.name = name.strip()
        manufacturer.description = description.strip() if description else None
        
        db.commit()
        db.refresh(manufacturer)
        
        # Логируем изменение в едином формате
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="Manufacturer",
            entity_id=manufacturer.id,
            details={
                "diff": {
                    "name": {
                        "old": old_name,
                        "new": manufacturer.name
                    },
                    "description": {
                        "old": old_description,
                        "new": manufacturer.description
                    }
                }
            }
        )
        
        return {
            "id": manufacturer.id,
            "name": manufacturer.name,
            "description": manufacturer.description,
            "message": "Производитель успешно обновлен"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Производитель с таким названием уже существует"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating manufacturer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении производителя: {str(e)}"
        )

@router.delete("/manufacturers/{manufacturer_id}")
async def delete_manufacturer(manufacturer_id: int, db: Session = Depends(get_db)):
    """Удалить производителя"""
    try:
        manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Производитель не найден")
        
        # Проверяем, используется ли производитель
        models_count = db.query(DeviceModel).filter(DeviceModel.manufacturer_id == manufacturer_id).count()
        
        if models_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить производителя. Используется в {models_count} моделях устройс��в"
            )
        
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="Manufacturer",
            entity_id=manufacturer.id,
            details={"name": manufacturer.name}
        )
        
        db.delete(manufacturer)
        db.commit()
        
        return {"message": "Производитель успешно удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting manufacturer: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении производителя: {str(e)}"
        )

# Эндпоинты для моделей устройств
@router.get("/device-models/{model_id}", response_model=dict)
async def get_device_model(model_id: int, db: Session = Depends(get_db)):
    """Получить одну модель устройства по ID"""
    device_model = db.query(DeviceModel).filter(DeviceModel.id == model_id).first()
    if not device_model:
        raise HTTPException(status_code=404, detail="Модель устройства не найдена")
    
    return {
        "id": device_model.id,
        "name": device_model.name,
        "manufacturer_id": device_model.manufacturer_id,
        "manufacturer_name": device_model.manufacturer.name if device_model.manufacturer else None,
        "asset_type_id": device_model.asset_type_id,
        "asset_type_name": device_model.asset_type.name if device_model.asset_type else None,
        "description": device_model.description
    }

@router.put("/device-models/{model_id}", response_model=dict)
async def update_device_model(
    model_id: int,
    name: str = Form(...),
    manufacturer_id: int = Form(...),
    asset_type_id: int = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновить модель устройства"""
    try:
        device_model = db.query(DeviceModel).filter(DeviceModel.id == model_id).first()
        if not device_model:
            raise HTTPException(status_code=404, detail="Модель устройства не найдена")
        
        # Проверяем существование производителя и типа актива
        manufacturer = db.query(Manufacturer).filter(Manufacturer.id == manufacturer_id).first()
        if not manufacturer:
            raise HTTPException(status_code=404, detail="Указанный производитель не найден")
            
        asset_type = db.query(AssetType).filter(AssetType.id == asset_type_id).first()
        if not asset_type:
            raise HTTPException(status_code=404, detail="Указанный тип актива не найден")
        
        # Сохраняем старые значения
        old_name = device_model.name
        old_manufacturer_id = device_model.manufacturer_id
        old_manufacturer_name = device_model.manufacturer.name if device_model.manufacturer else None
        old_asset_type_id = device_model.asset_type_id
        old_asset_type_name = device_model.asset_type.name if device_model.asset_type else None
        old_description = device_model.description
        
        # Обновляем модель устройства
        device_model.name = name.strip()
        device_model.manufacturer_id = manufacturer_id
        device_model.asset_type_id = asset_type_id
        device_model.description = description.strip() if description else None
        
        db.commit()
        db.refresh(device_model)
        
        # Получаем новые связанные объекты для логирования
        new_manufacturer = db.query(Manufacturer).get(manufacturer_id)
        new_asset_type = db.query(AssetType).get(asset_type_id)
        
        # Логируем действие в едином формате
        log_action(
            db=db,
            user_id=None,  # TODO: Заменить на ID аутентифицированного пользователя
            action_type="update",
            entity_type="DeviceModel",
            entity_id=device_model.id,
            details={
                "diff": {
                    "name": {
                        "old": old_name,
                        "new": device_model.name
                    },
                    "manufacturer": {
                        "old": {
                            "id": old_manufacturer_id,
                            "name": old_manufacturer_name
                        },
                        "new": {
                            "id": device_model.manufacturer_id,
                            "name": new_manufacturer.name if new_manufacturer else None
                        }
                    },
                    "asset_type": {
                        "old": {
                            "id": old_asset_type_id,
                            "name": old_asset_type_name
                        },
                        "new": {
                            "id": device_model.asset_type_id,
                            "name": new_asset_type.name if new_asset_type else None
                        }
                    },
                    "description": {
                        "old": old_description,
                        "new": device_model.description
                    }
                }
            }
        )
        
        return {
            "id": device_model.id,
            "name": device_model.name,
            "manufacturer_id": device_model.manufacturer_id,
            "manufacturer_name": new_manufacturer.name,
            "asset_type_id": device_model.asset_type_id,
            "asset_type_name": new_asset_type.name,
            "description": device_model.description,
            "message": "Модель устройства успешно обновлена"
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Модель устройства с таким названием уже существует"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating device model: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении модели устройства: {str(e)}"
        )

@router.delete("/device-models/{model_id}")
async def delete_device_model(model_id: int, db: Session = Depends(get_db)):
    """Удалить модель устройства"""
    try:
        device_model = db.query(DeviceModel).filter(DeviceModel.id == model_id).first()
        if not device_model:
            raise HTTPException(status_code=404, detail="Модель устройства не найдена")
        
        # Проверяем, используется ли модель
        from app.models import Device
        devices_count = db.query(Device).filter(Device.device_model_id == model_id).count()
        
        if devices_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Нельзя удалить модель устройства. Используется в {devices_count} устройствах"
            )
        
        log_action(
            db=db,
            user_id=None,
            action_type="delete",
            entity_type="DeviceModel",
            entity_id=device_model.id,
            details={"name": device_model.name}
        )
        
        db.delete(device_model)
        db.commit()
        
        return {"message": "Модель устройства успешно удалена"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting device model: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении модели устройства: {str(e)}"
        )