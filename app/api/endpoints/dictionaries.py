# app/api/endpoints/dictionaries.py
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_superuser_from_session,
    get_current_user_from_session,
)
from app.db.database import get_db
from app.models import (
    AssetType,
    Department,
    DeviceModel,
    DeviceStatus,
    Employee,
    Location,
    Manufacturer,
    Supplier,
    Tag,
    User,
)
from app.schemas.dictionary import (
    AssetTypeCreate,
    DepartmentCreate,
    DeviceModelCreate,
    DeviceStatusCreate,
    EmployeeCreate,
    LocationCreate,
    ManufacturerCreate,
    SupplierCreate,
)
from app.schemas.tag import TagCreate
from app.services.dictionary_service import DictionaryService

# --- ИЗМЕНЕНИЕ 1: Импортируем наше кастомное исключение ---
from app.services.exceptions import DuplicateError

logger = logging.getLogger(__name__)
router = APIRouter()


def get_dictionary_service() -> DictionaryService:
    return DictionaryService()


DICTIONARY_CONFIG = {
    'asset-types': {
        'model': AssetType,
        'schema': AssetTypeCreate,
        'service_method': 'create_asset_type',
    },
    'device-models': {
        'model': DeviceModel,
        'schema': DeviceModelCreate,
        'service_method': 'create_device_model',
    },
    'device-statuses': {
        'model': DeviceStatus,
        'schema': DeviceStatusCreate,
        'service_method': 'create_device_status',
    },
    'manufacturers': {
        'model': Manufacturer,
        'schema': ManufacturerCreate,
        'service_method': 'create_manufacturer',
    },
    'departments': {
        'model': Department,
        'schema': DepartmentCreate,
        'service_method': 'create_department',
    },
    'locations': {
        'model': Location,
        'schema': LocationCreate,
        'service_method': 'create_location',
    },
    'employees': {
        'model': Employee,
        'schema': EmployeeCreate,
        'service_method': 'create_employee',
    },
    'suppliers': {
        'model': Supplier,
        'schema': SupplierCreate,
        'service_method': 'create_supplier',
    },
    'tags': {
        'model': Tag,
        'schema': TagCreate,
        'service_method': 'create_tag',
    },
}


@router.post('/{dict_name}', status_code=status.HTTP_201_CREATED)
async def create_dictionary_entry(
    request: Request,
    dict_name: str,
    db: AsyncSession = Depends(get_db),
    service: DictionaryService = Depends(get_dictionary_service),
    current_user: User = Depends(get_current_superuser_from_session),
):
    if dict_name not in DICTIONARY_CONFIG:
        raise HTTPException(
            status_code=404, detail=f'Справочник "{dict_name}" не найден.'
        )

    config = DICTIONARY_CONFIG[dict_name]
    form_data = await request.form()

    # Собираем все поля из формы в словарь
    data_dict = {}
    for key, value in form_data.items():
        if value is not None and value != '':
            # Пробуем преобразовать числовые значения
            if key.endswith('_id'):
                try:
                    data_dict[key] = int(value)
                except (ValueError, TypeError):
                    data_dict[key] = value
            else:
                data_dict[key] = value

    try:
        schema_instance = config['schema'](**data_dict)
        service_method = getattr(service, config['service_method'])
        created_item = await service_method(db=db, data=schema_instance)
        return created_item
    # --- ИЗМЕНЕНИЕ 2: Добавляем обработку нашей кастомной ошибки ---
    except DuplicateError as e:
        # Ловим нашу ошибку и возвращаем 409 Conflict с понятным сообщением
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(
            f'Ошибка при создании записи в справочнике {dict_name}: {e}', exc_info=True
        )
        # Все остальные ошибки считаем ошибкой валидации или сервера
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка валидации или сохранения: {e}',
        )


@router.get('/{dict_name}')
async def get_dictionary_entries(
    dict_name: str,
    db: AsyncSession = Depends(get_db),
    service: DictionaryService = Depends(get_dictionary_service),
    current_user: User = Depends(get_current_user_from_session),
) -> list[dict[str, Any]]:
    if dict_name not in DICTIONARY_CONFIG:
        raise HTTPException(
            status_code=404, detail=f'Справочник "{dict_name}" не найден.'
        )

    model = DICTIONARY_CONFIG[dict_name]['model']
    items = await service.get_all(db, model)

    # Преобразуем SQLAlchemy модели в словари для корректной сериализации
    # Для device-models добавляем информацию о производителе
    if dict_name == 'device-models':
        return [
            {
                'id': item.id,
                'name': item.name,
                'manufacturer': {
                    'id': item.manufacturer.id,
                    'name': item.manufacturer.name,
                } if item.manufacturer else None,
            }
            for item in items
        ]
    return [{'id': item.id, 'name': item.name} for item in items]


@router.delete('/{dict_name}/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_dictionary_entry(
    dict_name: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser_from_session),
) -> None:
    """Удаляет запись из справочника через API."""
    if dict_name not in DICTIONARY_CONFIG:
        raise HTTPException(
            status_code=404, detail=f'Справочник "{dict_name}" не найден.'
        )

    # Для удаления используем специализированные сервисы, а не DictionaryService
    # Они содержат логику проверки зависимостей
    from app.services.asset_type_service import asset_type_service
    from app.services.department_service import department_service
    from app.services.device_model_service import device_model_service
    from app.services.device_status_service import device_status_service
    from app.services.employee_service import employee_service
    from app.services.exceptions import DeletionError
    from app.services.location_service import location_service
    from app.services.manufacturer_service import manufacturer_service
    from app.services.supplier_service import supplier_service
    from app.services.tag_service import tag_service

    service_map = {
        'asset-types': asset_type_service,
        'device-models': device_model_service,
        'device-statuses': device_status_service,
        'manufacturers': manufacturer_service,
        'suppliers': supplier_service,
        'departments': department_service,
        'locations': location_service,
        'employees': employee_service,
        'tags': tag_service,
    }

    service = service_map.get(dict_name)
    if not service:
        raise HTTPException(
            status_code=500,
            detail=f'Сервис для справочника {dict_name} не найден.',
        )

    try:
        # Используем ID текущего суперпользователя
        deleted_item = await service.delete(db, obj_id=item_id, user_id=current_user.id)
        if not deleted_item:
            raise HTTPException(
                status_code=404, detail='Запись не найдена.'
            )
    except DeletionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )


@router.get('/api/models/by-manufacturer/{manufacturer_id}', name='get_models_by_manufacturer')
async def get_models_by_manufacturer(
    manufacturer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_session),
):
    """Возвращает список моделей устройств для указанного производителя."""
    from sqlalchemy import select

    stmt = (
        select(DeviceModel)
        .where(DeviceModel.manufacturer_id == manufacturer_id)
        .order_by(DeviceModel.name)
    )
    result = await db.execute(stmt)
    models = result.scalars().all()

    return [{'id': m.id, 'name': m.name} for m in models]
