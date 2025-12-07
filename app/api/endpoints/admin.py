# app/api/endpoints/admin.py
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.database import get_db
from app.flash import flash
from app.models.user import User
from app.schemas.dictionary import (
    AssetTypeCreate,
    AssetTypeUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    DeviceModelCreate,
    DeviceModelUpdate,
    DeviceStatusCreate,
    DeviceStatusUpdate,
    DictionarySimpleCreate,
    DictionarySimpleUpdate,
    EmployeeCreate,
    EmployeeUpdate,
    LocationCreate,
    LocationUpdate,
)
from app.services.asset_type_service import asset_type_service
from app.services.department_service import department_service
from app.services.device_model_service import device_model_service
from app.services.device_status_service import device_status_service
from app.services.employee_service import employee_service
from app.services.exceptions import DeletionError, DuplicateError
from app.services.location_service import location_service
from app.services.manufacturer_service import manufacturer_service
from app.services.supplier_service import supplier_service
from app.services.tag_service import tag_service
from app.templating import templates

logger = logging.getLogger(__name__)
router = APIRouter()

DICTIONARY_CONFIG = {
    'asset-types': {
        'service': asset_type_service,
        'title': 'Типы активов',
        'icon': 'bi-box-seam',
        'description': 'Категории оборудования',
        'list_variable_name': 'asset_types',
        'template': 'admin/asset_types.html',
        'has_slug': True,
        'has_prefix': True,
    },
    'device-models': {
        'service': device_model_service,
        'title': 'Модели устройств',
        'icon': 'bi-laptop',
        'description': 'Конкретные модели техники',
        'list_variable_name': 'device_models',
        'template': 'admin/device_models.html',
        'has_slug': False,
        'has_prefix': False,
    },
    'device-statuses': {
        'service': device_status_service,
        'title': 'Статусы устройств',
        'icon': 'bi-check-circle',
        'description': 'Состояния активов',
        'list_variable_name': 'device_statuses',
        'template': 'admin/device_statuses.html',
        'has_slug': True,
        'has_prefix': False,
    },
    'manufacturers': {
        'service': manufacturer_service,
        'title': 'Производители',
        'icon': 'bi-building',
        'description': 'Бренды оборудования',
        'list_variable_name': 'manufacturers',
        'template': 'admin/manufacturers.html',
        'has_slug': False,
        'has_prefix': False,
    },
    'suppliers': {
        'service': supplier_service,
        'title': 'Поставщики',
        'icon': 'bi-truck',
        'description': 'Компании-поставщики',
        'list_variable_name': 'suppliers',
        'template': 'admin/suppliers.html',
        'has_slug': False,
        'has_prefix': False,
    },
    'departments': {
        'service': department_service,
        'title': 'Отделы',
        'icon': 'bi-diagram-3',
        'description': 'Структурные подразделения',
        'list_variable_name': 'departments',
        'template': 'admin/departments.html',
        'has_slug': True,
        'has_prefix': False,
    },
    'locations': {
        'service': location_service,
        'title': 'Местоположения',
        'icon': 'bi-geo-alt',
        'description': 'Кабинеты, офисы, склады',
        'list_variable_name': 'locations',
        'template': 'admin/locations.html',
        'has_slug': True,
        'has_prefix': False,
    },
    'employees': {
        'service': employee_service,
        'title': 'Сотрудники',
        'icon': 'bi-people',
        'description': 'Персонал организации',
        'list_variable_name': 'employees',
        'template': 'admin/employees.html',
        'has_slug': False,
        'has_prefix': False,
    },
    'tags': {
        'service': tag_service,
        'title': 'Теги',
        'icon': 'bi-tags',
        'description': 'Метки и свойства активов',
        'list_variable_name': 'tags',
        'template': 'admin/tags.html',
        'has_slug': False,
        'has_prefix': False,
    },
}


@router.get('/dictionaries', response_class=HTMLResponse, name='dictionaries_dashboard')
async def dictionaries_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    stats = {}
    for name, config in DICTIONARY_CONFIG.items():
        stats[name.replace('-', '_')] = await config['service'].get_count(db)
    return templates.TemplateResponse(
        'admin/dictionaries_dashboard.html',
        {
            'request': request,
            'stats': stats,
            'dictionaries': DICTIONARY_CONFIG,
            'title': 'Управление справочниками',
        },
    )


@router.get(
    '/dictionaries/{dictionary_type}',
    response_class=HTMLResponse,
    name='manage_dictionary',
)
async def manage_dictionary(
    request: Request,
    dictionary_type: str,
    db: AsyncSession = Depends(get_db),
    next: str | None = None,
):
    if dictionary_type not in DICTIONARY_CONFIG:
        return templates.TemplateResponse(
            'error.html',
            {'request': request, 'error': 'Справочник не найден.'},
            status_code=404,
        )

    config = DICTIONARY_CONFIG[dictionary_type]
    items = await config['service'].get_all(db)
    context = {
        'request': request,
        'title': config['title'],
        config['list_variable_name']: items,
        'next_url': next,  # Для кнопки "Вернуться к форме"
    }

    if dictionary_type == 'device-models':
        context['manufacturers'] = await manufacturer_service.get_all(db)
        context['asset_types'] = await asset_type_service.get_all(db)

    if dictionary_type == 'employees':
        context['departments'] = await department_service.get_all(db)

    return templates.TemplateResponse(config['template'], context)


@router.get(
    '/dictionaries/{dictionary_type}/quick-add',
    response_class=HTMLResponse,
    name='quick_add_dictionary_item_page',
)
async def quick_add_dictionary_item_page(
    request: Request,
    dictionary_type: str,
    next: str | None = None,
    current_user: User = Depends(deps.get_current_superuser_from_session),
):
    """Страница быстрого добавления записи в справочник (без модального окна)."""
    if dictionary_type not in DICTIONARY_CONFIG:
        return templates.TemplateResponse(
            'error.html',
            {'request': request, 'error': 'Справочник не найден.'},
            status_code=404,
        )

    config = DICTIONARY_CONFIG[dictionary_type]

    # Простые справочники со slug — поддерживаем quick-add
    # Сложные (employees, device-models, suppliers) — редирект на полную страницу
    if dictionary_type in ('employees', 'device-models', 'suppliers'):
        flash(request, 'Для этого справочника используйте полную форму.', 'info')
        return RedirectResponse(
            url=request.url_for('manage_dictionary', dictionary_type=dictionary_type),
            status_code=303,
        )

    return templates.TemplateResponse(
        'admin/quick_add.html',
        {
            'request': request,
            'title': f"Добавить: {config['title']}",
            'dictionary_type': dictionary_type,
            'next_url': next,
            'has_slug': config.get('has_slug', False),
            'has_prefix': config.get('has_prefix', False),
        },
    )


@router.post('/dictionaries/{dictionary_type}/quick-add', name='quick_add_dictionary_item')
async def quick_add_dictionary_item(
    request: Request,
    dictionary_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser_from_session),
):
    """Обработка формы быстрого добавления с редиректом обратно."""
    if dictionary_type not in DICTIONARY_CONFIG:
        return RedirectResponse(
            url=request.url_for('dictionaries_dashboard'), status_code=303
        )

    config = DICTIONARY_CONFIG[dictionary_type]
    service = config['service']
    form_data = await request.form()
    user_id = current_user.id

    # Получаем URL для возврата
    next_url = form_data.get('next')

    try:
        if dictionary_type == 'asset-types':
            schema = AssetTypeCreate.model_validate(form_data)
        elif dictionary_type == 'departments':
            schema = DepartmentCreate.model_validate(form_data)
        elif dictionary_type == 'locations':
            schema = LocationCreate.model_validate(form_data)
        elif dictionary_type == 'device-statuses':
            schema = DeviceStatusCreate.model_validate(form_data)
        else:
            schema = DictionarySimpleCreate.model_validate(form_data)

        await service.create(db, obj_in=schema, user_id=user_id)
        flash(request, "Запись успешно создана!", 'success')

    except ValidationError as e:
        errors = e.errors()
        error_message = '; '.join(
            [f"Поле '{err['loc'][0]}': {err['msg']}" for err in errors]
        )
        flash(request, f'Ошибка валидации: {error_message}', 'danger')
        # Возвращаем на форму quick-add с параметром next
        return RedirectResponse(
            url=f"{request.url_for('quick_add_dictionary_item_page', dictionary_type=dictionary_type)}?next={next_url or ''}",
            status_code=303,
        )

    except DuplicateError as e:
        flash(request, str(e), 'danger')
        return RedirectResponse(
            url=f"{request.url_for('quick_add_dictionary_item_page', dictionary_type=dictionary_type)}?next={next_url or ''}",
            status_code=303,
        )

    # Успешно — редирект назад
    if next_url:
        return RedirectResponse(url=next_url, status_code=303)

    return RedirectResponse(
        url=request.url_for('manage_dictionary', dictionary_type=dictionary_type),
        status_code=303,
    )


@router.post('/dictionaries/{dictionary_type}/add', name='create_dictionary_item')
async def create_dictionary_item(
    request: Request,
    dictionary_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser_from_session),
):
    if dictionary_type not in DICTIONARY_CONFIG:
        return RedirectResponse(
            url=request.url_for('dictionaries_dashboard'), status_code=303
        )

    config = DICTIONARY_CONFIG[dictionary_type]
    service = config['service']
    form_data = await request.form()
    user_id = current_user.id

    # Получаем URL для возврата (если есть)
    next_url = form_data.get('next')

    try:
        if dictionary_type == 'asset-types':
            schema = AssetTypeCreate.model_validate(form_data)
        elif dictionary_type == 'device-models':
            schema = DeviceModelCreate.model_validate(form_data)
        elif dictionary_type == 'employees':
            schema = EmployeeCreate.model_validate(form_data)
        elif dictionary_type == 'departments':
            schema = DepartmentCreate.model_validate(form_data)
        elif dictionary_type == 'locations':
            schema = LocationCreate.model_validate(form_data)
        elif dictionary_type == 'device-statuses':
            schema = DeviceStatusCreate.model_validate(form_data)
        else:
            schema = DictionarySimpleCreate.model_validate(form_data)

        await service.create(db, obj_in=schema, user_id=user_id)
        flash(
            request,
            f"Запись в справочнике '{config['title']}' успешно создана.",
            'success',
        )

        # Если есть next — редирект обратно на форму актива
        if next_url:
            return RedirectResponse(url=next_url, status_code=303)

    except ValidationError as e:
        errors = e.errors()
        error_message = '; '.join(
            [f"Поле '{err['loc'][0]}': {err['msg']}'" for err in errors]
        )
        flash(request, f'Ошибка валидации: {error_message}', 'danger')

    except DuplicateError as e:
        flash(request, str(e), 'danger')

    # По умолчанию — редирект на страницу справочника (с сохранением next если есть)
    redirect_url = request.url_for('manage_dictionary', dictionary_type=dictionary_type)
    if next_url:
        redirect_url = f"{redirect_url}?next={next_url}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post(
    '/dictionaries/{dictionary_type}/{item_id}/edit', name='edit_dictionary_item'
)
async def edit_dictionary_item(
    request: Request,
    dictionary_type: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser_from_session),
):
    if dictionary_type not in DICTIONARY_CONFIG:
        return RedirectResponse(
            url=request.url_for('dictionaries_dashboard'), status_code=303
        )

    config = DICTIONARY_CONFIG[dictionary_type]
    service = config['service']
    form_data = await request.form()
    user_id = current_user.id

    try:
        if dictionary_type == 'asset-types':
            schema = AssetTypeUpdate.model_validate(form_data)
        elif dictionary_type == 'device-models':
            schema = DeviceModelUpdate.model_validate(form_data)
        elif dictionary_type == 'employees':
            schema = EmployeeUpdate.model_validate(form_data)
        elif dictionary_type == 'departments':
            schema = DepartmentUpdate.model_validate(form_data)
        elif dictionary_type == 'locations':
            schema = LocationUpdate.model_validate(form_data)
        elif dictionary_type == 'device-statuses':
            schema = DeviceStatusUpdate.model_validate(form_data)
        else:
            schema = DictionarySimpleUpdate.model_validate(form_data)

        await service.update(db, obj_id=item_id, obj_in=schema, user_id=user_id)
        flash(
            request,
            f"Запись в справочнике '{config['title']}' успешно обновлена.",
            'success',
        )

    except ValidationError as e:
        errors = e.errors()
        error_message = '; '.join(
            [f"Поле '{err['loc'][0]}': {err['msg']}" for err in errors]
        )
        flash(request, f'Ошибка валидации: {error_message}', 'danger')

    except DuplicateError as e:
        flash(request, str(e), 'danger')

    return RedirectResponse(
        url=request.url_for('manage_dictionary', dictionary_type=dictionary_type),
        status_code=303,
    )


@router.post(
    '/dictionaries/{dictionary_type}/{item_id}/delete', name='delete_dictionary_item'
)
async def delete_dictionary_item(
    request: Request,
    dictionary_type: str,
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_superuser_from_session),
):
    if dictionary_type not in DICTIONARY_CONFIG:
        return RedirectResponse(
            url=request.url_for('dictionaries_dashboard'), status_code=303
        )

    config = DICTIONARY_CONFIG[dictionary_type]
    service = config['service']
    user_id = current_user.id

    try:
        deleted_item = await service.delete(db, obj_id=item_id, user_id=user_id)
        if deleted_item:
            flash(
                request,
                f"Запись '{getattr(deleted_item, 'name', getattr(deleted_item, 'full_name', ''))}' успешно удалена.",
                'success',
            )
    except DeletionError as e:
        flash(request, str(e), 'danger')

    return RedirectResponse(
        url=request.url_for('manage_dictionary', dictionary_type=dictionary_type),
        status_code=303,
    )
