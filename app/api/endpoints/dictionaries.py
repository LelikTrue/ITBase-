# app/api/endpoints/dictionaries.py

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.dictionary import (
    AssetTypeCreate,
    AssetTypeResponse,
    AssetTypeUpdate,
    DeviceModelCreate,
    DeviceModelResponse,
    DeviceModelUpdate,
    DictionarySimpleCreate,
    DictionarySimpleResponse,
    DictionarySimpleUpdate,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.asset_type_service import AssetTypeService
from app.services.department_service import DepartmentService

# --- Новые импорты ---
from app.services.device_model_service import DeviceModelService
from app.services.device_status_service import DeviceStatusService
from app.services.employee_service import EmployeeService
from app.services.exceptions import DeletionError, DuplicateError, NotFoundError
from app.services.location_service import LocationService
from app.services.manufacturer_service import ManufacturerService
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import TagService

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация APIRouter
router = APIRouter(prefix='/api/dictionaries', tags=['dictionaries'])

# --- Создаем экземпляры сервисов ---
asset_type_service = AssetTypeService()
device_status_service = DeviceStatusService()
manufacturer_service = ManufacturerService()
department_service = DepartmentService()
location_service = LocationService()
device_model_service = DeviceModelService()
employee_service = EmployeeService()
tag_service = TagService()


# === Эндпоинты для типов активов (AssetType) ===

@router.get('/asset-types', response_model=list[DictionarySimpleResponse])
async def get_asset_types(db: AsyncSession = Depends(get_db)):
    """Получить список всех типов активов"""
    try:
        asset_types = await asset_type_service.get_all(db)
        return asset_types
    except Exception as e:
        logger.error(f'Error getting asset types: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при получении типов активов.')


@router.post('/asset-types', response_model=AssetTypeResponse, status_code=status.HTTP_201_CREATED) # <--- ИЗМЕНЕНИЕ
async def create_asset_type(
        db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    prefix: str = Form(...),
    description: str | None = Form(None)
):
    """Создать новый тип актива"""
    try:
        # Вручную создаем новую, специализированную Pydantic-схему
        asset_type_data = AssetTypeCreate(name=name, prefix=prefix, description=description)

        user_id = 1
        # Теперь этот вызов будет использовать наш новый, специализированный сервис
        return await asset_type_service.create(db, asset_type_data, user_id)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating asset type: {e}', exc_info=True)
        # Возвращаем 500, чтобы увидеть в консоли, если что-то пошло не так
        raise HTTPException(status_code=500, detail=f'Внутренняя ошибка сервера: {e}')


@router.put('/asset-types/{asset_type_id}', response_model=AssetTypeResponse)
async def update_asset_type(
    asset_type_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    prefix: str = Form(...),
    description: str | None = Form(None)
):
    """Обновить тип актива"""
    try:
        # Используем новую, специализированную схему
        asset_type_data = AssetTypeUpdate(
            name=name,
            prefix=prefix,
            description=description
        )

        user_id = 1
        updated_asset_type = await asset_type_service.update(db, asset_type_id, asset_type_data, user_id)
        if updated_asset_type is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Тип актива не найден.')
        return updated_asset_type
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating asset type: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при обновлении типа актива.')

@router.delete('/asset-types/{asset_type_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_type(asset_type_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить тип актива"""
    try:
        user_id = 1 # TODO: Заменить на реального пользователя
        deleted_item = await asset_type_service.delete(db, asset_type_id, user_id)
        if deleted_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Тип актива не найден.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting asset type: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

# Эндпоинты для моделей устройств (DeviceModel)
@router.get('/device-models', response_model=list[DeviceModelResponse])
async def get_device_models(db: AsyncSession = Depends(get_db)):
    """Получить список всех моделей устройств"""
    try:
        device_models = await device_model_service.get_all(db)
        return device_models
    except Exception as e:
        logger.error(f'Error getting device models: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Ошибка при получении моделей устройств.')

@router.get('/device-models/{model_id}', response_model=DeviceModelResponse)
async def get_device_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """Получить одну модель устройства по ID"""
    device_model = await device_model_service.get_by_id(db, model_id)
    if not device_model:
        raise HTTPException(status_code=404, detail='Модель устройства не найдена')
    return device_model

@router.post('/device-models', response_model=DeviceModelResponse, status_code=status.HTTP_201_CREATED)
async def create_device_model(
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    manufacturer_id: int = Form(...),
    asset_type_id: int = Form(...),
    description: str | None = Form(None)
):
    """Создать новую модель устройства"""
    try:
        # Вручную создаем Pydantic-схему из явных полей формы
        device_model_data = DeviceModelCreate(
            name=name,
            manufacturer_id=manufacturer_id,
            asset_type_id=asset_type_id,
            description=description
        )

        user_id = 1  # TODO: Заменить на ID аутентифицированного пользователя

        new_model = await device_model_service.create(db, device_model_data, user_id)

        # Для ответа нам нужно подгрузить связанные сущности
        await db.refresh(new_model, attribute_names=['manufacturer', 'asset_type'])

        return new_model

    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating device model: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при создании модели устройства.')

@router.put('/device-models/{model_id}', response_model=DeviceModelResponse)
async def update_device_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    manufacturer_id: int = Form(...),
    asset_type_id: int = Form(...),
    description: str | None = Form(None)
):
    """Обновить модель устройства"""
    try:
        model_data = DeviceModelUpdate(
            name=name, manufacturer_id=manufacturer_id, asset_type_id=asset_type_id, description=description
        )
        user_id = 1  # TODO: Заменить на ID аутентифицированного пользователя

        updated_model = await device_model_service.update(db, model_id, model_data, user_id)

        if updated_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Модель устройства не найдена.')

        # Обновляем связанные данные для корректного ответа
        await db.refresh(updated_model, attribute_names=['manufacturer', 'asset_type'])

        return updated_model

    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating device model: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при обновлении модели устройства.')

@router.delete('/device-models/{model_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить модель устройства"""
    try:
        user_id = 1  # TODO: Заменить на ID аутентифицированного пользователя
        deleted_model = await device_model_service.delete(db, model_id, user_id)
        if deleted_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Модель устройства не найдена.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting device model: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при удалении модели устройства.')

# === Эндпоинты для статусов устройств (DeviceStatus) ===

@router.get('/device-statuses', response_model=list[DictionarySimpleResponse])
async def get_device_statuses(db: AsyncSession = Depends(get_db)):
    """Получить список всех статусов устройств"""
    items = await device_status_service.get_all(db)
    return items

@router.post('/device-statuses', response_model=DictionarySimpleResponse, status_code=status.HTTP_201_CREATED)
async def create_device_status(
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Создать новый статус устройства"""
    try:
        status_data = DictionarySimpleCreate(name=name, description=description)
        user_id = 1 # TODO: Заменить на реального пользователя
        return await device_status_service.create(db, status_data, user_id)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating device status: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.put('/device-statuses/{status_id}', response_model=DictionarySimpleResponse)
async def update_device_status(
    status_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Обновить статус устройства"""
    try:
        status_data = DictionarySimpleUpdate(name=name, description=description)

        user_id = 1 # TODO: Заменить на реального пользователя
        updated_item = await device_status_service.update(db, status_id, status_data, user_id)
        if updated_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Статус не найден.')
        return updated_item
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating device status: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.delete('/device-statuses/{status_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_status(status_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить статус устройства"""
    try:
        user_id = 1 # TODO: Заменить на реального пользователя
        deleted_item = await device_status_service.delete(db, status_id, user_id)
        if deleted_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Статус не найден.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting device status: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')


# === Эндпоинты для производителей (Manufacturer) ===

@router.get('/manufacturers', response_model=list[DictionarySimpleResponse])
async def get_manufacturers(db: AsyncSession = Depends(get_db)):
    """Получить список всех производителей"""
    items = await manufacturer_service.get_all(db)
    return items

@router.post('/manufacturers', response_model=DictionarySimpleResponse, status_code=status.HTTP_201_CREATED)
async def create_manufacturer(
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Создать нового производителя"""
    try:
        manufacturer_data = DictionarySimpleCreate(name=name, description=description)
        user_id = 1 # TODO: Заменить на реального пользователя
        return await manufacturer_service.create(db, manufacturer_data, user_id)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating manufacturer: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.put('/manufacturers/{manufacturer_id}', response_model=DictionarySimpleResponse)
async def update_manufacturer(
    manufacturer_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Обновить производителя"""
    try:
        manufacturer_data = DictionarySimpleUpdate(name=name, description=description)

        user_id = 1 # TODO: Заменить на реального пользователя
        updated_item = await manufacturer_service.update(db, manufacturer_id, manufacturer_data, user_id)
        if updated_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Производитель не найден.')
        return updated_item
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating manufacturer: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.delete('/manufacturers/{manufacturer_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_manufacturer(manufacturer_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить производителя"""
    try:
        user_id = 1 # TODO: Заменить на реального пользователя
        deleted_item = await manufacturer_service.delete(db, manufacturer_id, user_id)
        if deleted_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Производитель не найден.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting manufacturer: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')


# === Эндпоинты для отделов (Department) ===

@router.get('/departments', response_model=list[DictionarySimpleResponse])
async def get_departments(db: AsyncSession = Depends(get_db)):
    """Получить список всех отделов"""
    items = await department_service.get_all(db)
    return items

@router.post('/departments', response_model=DictionarySimpleResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Создать новый отдел"""
    try:
        department_data = DictionarySimpleCreate(name=name, description=description)
        user_id = 1 # TODO: Заменить на реального пользователя
        return await department_service.create(db, department_data, user_id)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating department: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.put('/departments/{department_id}', response_model=DictionarySimpleResponse)
async def update_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Обновить отдел"""
    try:
        department_data = DictionarySimpleUpdate(name=name, description=description)

        user_id = 1 # TODO: Заменить на реального пользователя
        updated_item = await department_service.update(db, department_id, department_data, user_id)
        if updated_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Отдел не найден.')
        return updated_item
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating department: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.delete('/departments/{department_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(department_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить отдел"""
    try:
        user_id = 1 # TODO: Заменить на реального пользователя
        deleted_item = await department_service.delete(db, department_id, user_id)
        if deleted_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Отдел не найден.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting department: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')


# === Эндпоинты для местоположений (Location) ===

@router.get('/locations', response_model=list[DictionarySimpleResponse])
async def get_locations(db: AsyncSession = Depends(get_db)):
    """Получить список всех местоположений"""
    items = await location_service.get_all(db)
    return items

@router.post('/locations', response_model=DictionarySimpleResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    # --- НАЧАЛО ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ---
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
    # --- КОНЕЦ ФИНАЛЬНОГО ИСПРАВЛЕНИЯ ---
):
    """Создать новое местоположение"""
    try:
        # Вручную создаем Pydantic-схему из полученных данных формы.
        # Это явный и надежный способ.
        location_data = DictionarySimpleCreate(name=name, description=description)

        user_id = 1 # TODO: Заменить на реального пользователя
        return await location_service.create(db, location_data, user_id)

    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating location: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.put('/locations/{location_id}', response_model=DictionarySimpleResponse)
async def update_location(
    location_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Обновить местоположение"""
    try:
        location_data = DictionarySimpleUpdate(name=name, description=description)

        user_id = 1 # TODO: Заменить на реального пользователя
        updated_item = await location_service.update(db, location_id, location_data, user_id)
        if updated_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Местоположение не найдено.')
        return updated_item
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating location: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.delete('/locations/{location_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(location_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить местоположение"""
    try:
        user_id = 1 # TODO: Заменить на реального пользователя
        deleted_item = await location_service.delete(db, location_id, user_id)
        if deleted_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Местоположение не найдено.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting location: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

# === Эндпоинты для сотрудников (Employee) ===

@router.get('/employees', response_model=list[EmployeeResponse])
async def get_employees(db: AsyncSession = Depends(get_db)):
    """Получить список всех сотрудников"""
    employees = await employee_service.get_all(db)
    return employees

@router.post('/employees', response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    # --- НАЧАЛО ИЗМЕНЕНИЙ ---
    db: AsyncSession = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    patronymic: str | None = Form(None),
    employee_id: str | None = Form(None),
    email: EmailStr | None = Form(None),
    phone_number: str | None = Form(None)
    # --- КОНЕЦ ИЗМЕНЕНИЙ ---
):
    """Создать нового сотрудника"""
    try:
        # Вручную создаем Pydantic-схему
        employee_data = EmployeeCreate(
            last_name=last_name,
            first_name=first_name,
            patronymic=patronymic,
            employee_id=employee_id,
            email=email,
            phone_number=phone_number
        )

        user_id = 1 # TODO: Заменить на ID аутентифицированного пользователя
        return await employee_service.create(db, employee_data, user_id)

    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating employee: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при создании сотрудника.')

@router.put('/employees/{employee_id}', response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    patronymic: str | None = Form(None),
    employee_id_str: str | None = Form(None, alias='employee_id'), # Переименовано, чтобы избежать конфликта с employee_id из пути
    email: EmailStr | None = Form(None),
    phone_number: str | None = Form(None)
):
    """Обновить данные сотрудника"""
    try:
        employee_data = EmployeeUpdate(
            last_name=last_name, first_name=first_name, patronymic=patronymic,
            employee_id=employee_id_str, email=email, phone_number=phone_number
        )
        user_id = 1 # TODO: Заменить на ID аутентифицированного пользователя
        updated_employee = await employee_service.update(db, employee_id, employee_data, user_id)
        if updated_employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Сотрудник не найден.')
        return updated_employee
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating employee: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

@router.delete('/employees/{employee_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить сотрудника"""
    try:
        user_id = 1 # TODO: Заменить на ID аутентифицированного пользователя
        deleted_employee = await employee_service.delete(db, employee_id, user_id)
        if deleted_employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Сотрудник не найден.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting employee: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')

# === Эндпоинты для Тегов (Tags) ===

@router.get('/tags', response_model=list[TagResponse])
async def get_tags(db: AsyncSession = Depends(get_db)):
    """Получить список всех тегов"""
    try:
        items = await tag_service.get_all(db)
        return items
    except Exception as e:
        logger.error(f'Error getting tags: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Ошибка при получении списка тегов.')

@router.post('/tags', response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Создать новый тег"""
    try:
        tag_data = TagCreate(name=name, description=description)
        user_id = 1 # TODO: Заменить на реального пользователя
        return await tag_service.create(db, tag_data, user_id)
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error creating tag: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при создании тега.')

@router.put('/tags/{tag_id}', response_model=TagResponse)
async def update_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    name: str = Form(...),
    description: str | None = Form(None)
):
    """Обновить тег"""
    try:
        tag_data = TagUpdate(name=name, description=description)
        user_id = 1 # TODO: Заменить на реального пользователя
        updated_item = await tag_service.update(db, tag_id, tag_data, user_id)
        if updated_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Тег не найден.')
        return updated_item
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error updating tag: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера при обновлении тега.')

@router.delete('/tags/{tag_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить тег"""
    try:
        user_id = 1 # TODO: Заменить на реального пользователя
        deleted_item = await tag_service.delete(db, tag_id, user_id)
        if deleted_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Тег не найден.')
    except DeletionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(f'Error deleting tag: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Внутренняя ошибка сервера.')
