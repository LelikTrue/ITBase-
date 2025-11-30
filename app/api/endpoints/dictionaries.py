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
        'modal_title': 'Добавить тип актива',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'prefix',
                'label': 'Префикс',
                'type': 'text',
                'required': True,
                'maxlength': 10,
                'placeholder': 'Напр. PC, MONI, PRNT',
                'help_text': 'Короткий код для инвентарных номеров (до 10 символов).',
            },
            {
                'name': 'description',
                'label': 'Описание',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'device-models': {
        'model': DeviceModel,
        'schema': DeviceModelCreate,
        'service_method': 'create_device_model',
        'modal_title': 'Добавить модель',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'manufacturer_id',
                'label': 'Производитель',
                'type': 'select',
                'required': True,
                'options_from': 'manufacturers',
            },
            {
                'name': 'asset_type_id',
                'label': 'Тип актива',
                'type': 'select',
                'required': True,
                'options_from': 'asset-types',
            },
            {
                'name': 'description',
                'label': 'Описание',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'device-statuses': {
        'model': DeviceStatus,
        'schema': DeviceStatusCreate,
        'service_method': 'create_device_status',
        'modal_title': 'Добавить статус',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'description',
                'label': 'Описание',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'manufacturers': {
        'model': Manufacturer,
        'schema': ManufacturerCreate,
        'service_method': 'create_manufacturer',
        'modal_title': 'Добавить производителя',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'description',
                'label': 'Описание',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'departments': {
        'model': Department,
        'schema': DepartmentCreate,
        'service_method': 'create_department',
        'modal_title': 'Добавить отдел',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'description',
                'label': 'Описание',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'locations': {
        'model': Location,
        'schema': LocationCreate,
        'service_method': 'create_location',
        'modal_title': 'Добавить расположение',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'description',
                'label': 'Описание',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'employees': {
        'model': Employee,
        'schema': EmployeeCreate,
        'service_method': 'create_employee',
        'modal_title': 'Добавить сотрудника',
        'form_fields': [
            {'name': 'last_name', 'label': 'Фамилия', 'type': 'text', 'required': True},
            {'name': 'first_name', 'label': 'Имя', 'type': 'text', 'required': True},
            {
                'name': 'patronymic',
                'label': 'Отчество',
                'type': 'text',
                'required': False,
            },
            {
                'name': 'employee_id',
                'label': 'Табельный номер',
                'type': 'text',
                'required': False,
            },
            {
                'name': 'position',
                'label': 'Должность',
                'type': 'text',
                'required': False,
            },
            {
                'name': 'department_id',
                'label': 'ID Отдела',
                'type': 'number',
                'required': False,
            },
            {'name': 'email', 'label': 'Email', 'type': 'email', 'required': False},
            {
                'name': 'phone_number',
                'label': 'Телефон',
                'type': 'text',
                'required': False,
            },
        ],
    },
    'suppliers': {
        'model': Supplier,
        'schema': SupplierCreate,
        'service_method': 'create_supplier',
        'modal_title': 'Добавить поставщика',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
            {
                'name': 'contact_person',
                'label': 'Контактное лицо',
                'type': 'text',
                'required': False,
            },
            {'name': 'phone', 'label': 'Телефон', 'type': 'text', 'required': False},
            {'name': 'email', 'label': 'Email', 'type': 'email', 'required': False},
            {
                'name': 'address',
                'label': 'Адрес',
                'type': 'textarea',
                'required': False,
            },
        ],
    },
    'tags': {
        'model': Tag,
        'schema': TagCreate,
        'service_method': 'create_tag',
        'modal_title': 'Добавить тег',
        'form_fields': [
            {'name': 'name', 'label': 'Название', 'type': 'text', 'required': True},
        ],
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

    data_dict = {}
    field_names = [field['name'] for field in config['form_fields']]
    for field_name in field_names:
        value = form_data.get(field_name)
        if value is not None:
            data_dict[field_name] = value

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

