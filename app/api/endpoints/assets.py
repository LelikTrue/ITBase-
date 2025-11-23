import csv
import io
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.flash import flash, get_flashed_messages
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.services.device_service import DeviceService
from app.services.exceptions import (
    DeletionError,
    DeviceNotFoundException,
    DuplicateDeviceError,
    NotFoundError,
)
from app.templating import templates
from app.utils.helpers import safe_int

# ИМПОРТИРУЕМ НАШУ КОНФИГУРАЦИЮ ИЗ СОСЕДНЕГО ФАЙЛА
from .dictionaries import DICTIONARY_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter()

def get_device_service() -> DeviceService:
    return DeviceService()

@router.get('/assets-list', response_class=HTMLResponse, name='read_assets')
async def read_assets(
    request: Request,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    asset_type_id: str | None = Query(None),
    status_id: str | None = Query(None),
    department_id: str | None = Query(None),
    location_id: str | None = Query(None),
    manufacturer_id: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_order: str = Query('asc'),
):
    """Отображает список активов с фильтрацией, сортировкой и пагинацией."""
    try:
        filters_dict = {
            'search': search,
            'asset_type_id': safe_int(asset_type_id),
            'status_id': safe_int(status_id),
            'department_id': safe_int(department_id),
            'location_id': safe_int(location_id),
            'manufacturer_id': safe_int(manufacturer_id),
        }

        paginated_devices_db, total_devices = await device_service.get_devices_with_filters(
            db=db, page=page, page_size=page_size, sort_by=sort_by,
            sort_order=sort_order, **filters_dict
        )
        paginated_devices = [AssetResponse.model_validate(d, from_attributes=True) for d in paginated_devices_db]
        form_data = await device_service.get_all_dictionaries_for_form(db)
        query_params = request.query_params._dict.copy()
        query_params.pop('page', None)

        context = {
            'request': request,
            'devices': paginated_devices,
            'total_devices': total_devices,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_devices + page_size - 1) // page_size,
            'title': 'Список активов',
            **form_data,
            'endpoint_name': 'read_assets',
            'filters': {**filters_dict, 'page_size': page_size, 'sort_by': sort_by, 'sort_order': sort_order},
            'query_params': query_params,
        }
        return templates.TemplateResponse('assets_list.html', context)
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при загрузке списка активов: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Ошибка базы данных при загрузке активов.')

@router.get('/dashboard', response_class=HTMLResponse, name='dashboard')
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    """Отображает дашборд с аналитикой."""
    try:
        stats = await device_service.get_dashboard_stats(db)
        context = {
            'request': request,
            'title': 'Дашборд - IT Asset Tracker',
            **stats
        }
        return templates.TemplateResponse('dashboard.html', context)
    except SQLAlchemyError as e:
        logger.error(f'Ошибка при загрузке дашборда: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Ошибка базы данных при загрузке статистики.')

@router.get('/export/csv', name='export_assets_csv')
async def export_assets_csv(
    request: Request,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service),
    search: str | None = Query(None),
    asset_type_id: str | None = Query(None),
    status_id: str | None = Query(None),
    department_id: str | None = Query(None),
    location_id: str | None = Query(None),
    manufacturer_id: str | None = Query(None),
):
    """Экспортирует отфильтрованный список активов в CSV файл."""
    try:
        filters_dict = {
            'search': search, 'asset_type_id': safe_int(asset_type_id),
            'status_id': safe_int(status_id), 'department_id': safe_int(department_id),
            'location_id': safe_int(location_id), 'manufacturer_id': safe_int(manufacturer_id),
        }
        devices_db, _ = await device_service.get_devices_with_filters(
            db=db, page=1, page_size=1_000_000, **filters_dict
        )
        devices = [AssetResponse.model_validate(d, from_attributes=True) for d in devices_db]
        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        headers = [
            'ID', 'Инвентарный номер', 'Серийный номер', 'MAC-адрес', 'Тип', 'Производитель',
            'Модель', 'Статус', 'Отдел', 'Локация', 'Сотрудник', 'Дата покупки', 'Окончание гарантии'
        ]
        writer.writerow(headers)
        for device in devices:
            writer.writerow([
                device.id, device.inventory_number, device.serial_number, device.mac_address,
                device.asset_type.name,
                device.device_model.manufacturer.name,
                device.device_model.name,
                device.status.name,
                device.department.name if device.department else '',
                device.location.name if device.location else '',
                f'{device.employee.last_name} {device.employee.first_name}' if device.employee else '',
                device.purchase_date, device.warranty_end_date
            ])
        output.seek(0)
        filename = f"assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(io.StringIO(output.getvalue()), media_type='text/csv',
                                 headers={'Content-Disposition': f'attachment; filename="{filename}"'})
    except Exception as e:
        logger.error(f'Ошибка при экспорте в CSV: {e}', exc_info=True)
        flash(request, f'Ошибка при экспорте в CSV: {e}', 'danger')
        return RedirectResponse(url=request.url_for('read_assets'), status_code=status.HTTP_303_SEE_OTHER)

@router.get('/add', response_class=HTMLResponse, name='add_asset_form')
async def add_asset_form(request: Request, db: AsyncSession = Depends(get_db), device_service: DeviceService = Depends(get_device_service)):
    submitted_data = {}
    validation_errors = {}
    flashed_messages = get_flashed_messages(request)
    for msg in flashed_messages:
        if msg.get('category') == 'validation':
            if msg['message'].get('submitted_data'):
                submitted_data = msg['message']['submitted_data']
            if msg['message'].get('errors'):
                validation_errors = msg['message']['errors']

    asset = type('Asset', (), submitted_data)() if submitted_data else None
    try:
        form_data_for_selects = await device_service.get_all_dictionaries_for_form(db)
        all_tags = await device_service.get_all_tags(db)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных для формы 'add_asset': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Ошибка при загрузке данных для формы.')

    context = {
        'request': request,
        'title': 'Добавить актив',
        **form_data_for_selects,
        'all_tags': all_tags,
        'asset': asset,
        'errors': validation_errors,
        # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Передаем конфигурацию в шаблон ---
        'dictionary_config': DICTIONARY_CONFIG,
    }
    return templates.TemplateResponse('add_asset.html', context)

@router.post('/create', response_class=RedirectResponse, name='create_asset')
async def create_asset(
    request: Request,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service),
):
    form_data = await request.form()
    form_dict = dict(form_data)
    tag_ids_str = form_data.getlist('tag_ids')
    tag_ids = [int(tag_id) for tag_id in tag_ids_str if tag_id.isdigit()]
    form_dict['tag_ids'] = tag_ids

    # Логируем полученные данные для отладки
    logger.debug(f'Получены данные формы создания актива:')
    logger.debug(f'  Все ключи: {list(form_data.keys())}')
    logger.debug(f'  form_dict: {form_dict}')
    logger.debug(f'  Обязательные поля: name={form_dict.get("name")}, '
                 f'asset_type_id={form_dict.get("asset_type_id")}, '
                 f'device_model_id={form_dict.get("device_model_id")}, '
                 f'status_id={form_dict.get("status_id")}')

    try:
        asset_data = AssetCreate(**form_dict)
        await device_service.create_device(db=db, asset_data=asset_data, user_id=1)
        flash(request, 'Актив успешно добавлен!', 'success')
        return RedirectResponse(
            url=request.url_for('read_assets'), status_code=status.HTTP_303_SEE_OTHER
        )
    except ValidationError as e:
        logger.warning(f'Ошибка валидации при создании актива: {e.errors()}')
        error_messages = []
        for error in e.errors():
            field = error['loc'][0] if error['loc'] else 'unknown'
            msg = error['msg']
            error_messages.append(f'{field}: {msg}')
        flash(
            request,
            {
                'errors': {'general': 'Пожалуйста, заполните все обязательные поля'},
                'submitted_data': form_dict,
            },
            'validation',
        )
    except (DuplicateDeviceError, NotFoundError) as e:
        logger.warning(f'Ошибка бизнес-логики при создании актива: {e}')
        flash(
            request,
            {'errors': {'general': str(e)}, 'submitted_data': form_dict},
            'validation',
        )
    except Exception as e:
        logger.error(f'Непредвиденная ошибка при создании актива: {e}', exc_info=True)
        flash(
            request,
            {
                'errors': {'general': f'Произошла непредвиденная ошибка: {e}'},
                'submitted_data': form_dict,
            },
            'validation',
        )
    return RedirectResponse(
        url=request.url_for('add_asset_form'), status_code=status.HTTP_303_SEE_OTHER
    )

@router.get('/edit/{device_id}', response_class=HTMLResponse, name='edit_asset')
async def edit_asset(
    request: Request, device_id: int, db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
):
    device = await device_service.get_device_with_relations(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail='Устройство не найдено')
    try:
        form_data = await device_service.get_all_dictionaries_for_form(db)
    except Exception as e:
        logger.error(f'Ошибка при загрузке данных для формы редактирования: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Ошибка при загрузке данных для формы.')
    existing_tags_data = [{'id': tag.id, 'name': tag.name} for tag in device.tags]
    return templates.TemplateResponse(
        'edit_asset.html',
        {
            'request': request, 'device': device, **form_data,
            'existing_tags_data': existing_tags_data,
            'title': f'Редактировать актив #{device.id}',
            # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Передаем конфигурацию и в форму редактирования ---
            'dictionary_config': DICTIONARY_CONFIG,
        }
    )

@router.post('/update/{device_id}', response_class=RedirectResponse, name='update_asset')
async def update_asset(
    request: Request,
    device_id: int,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service),
):
    form_data = await request.form()
    form_dict = dict(form_data)
    tag_ids_str = form_data.getlist('tag_ids')
    tag_ids = [int(tag_id) for tag_id in tag_ids_str if tag_id.isdigit()]
    form_dict['tag_ids'] = tag_ids
    try:
        update_data = AssetUpdate(**form_dict)
        updated_device = await device_service.update_device_with_audit(
            db=db, device_id=device_id, update_data=update_data, user_id=1
        )
        if not updated_device:
            raise DeviceNotFoundException('Актив не найден')
        flash(request, 'Актив успешно обновлен!', 'success')
        return RedirectResponse(url=request.url_for('read_assets'), status_code=status.HTTP_303_SEE_OTHER)
    except (DeviceNotFoundException, DuplicateDeviceError, NotFoundError) as e:
        logger.warning(f'Ошибка бизнес-логики при обновлении актива {device_id}: {e}')
        flash(request, {'errors': {'general': str(e)}, 'submitted_data': form_dict}, 'validation')
    except Exception as e:
        logger.error(f'Ошибка при обновлении актива {device_id}: {e}', exc_info=True)
        flash(request, {'errors': {'general': f'Произошла непредвиденная ошибка: {e}'}, 'submitted_data': form_dict}, 'validation')
    return RedirectResponse(url=request.url_for('edit_asset', device_id=device_id), status_code=status.HTTP_303_SEE_OTHER)

@router.post('/delete/{device_id}', name='delete_asset')
async def delete_asset(
    request: Request,
    device_id: int,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service)
) -> Response:
    try:
        await device_service.delete_device_with_audit(db=db, device_id=device_id, user_id=1)
        flash(request, 'Актив успешно удален.', 'success')
    except DeviceNotFoundException as e:
        logger.warning(f'Попытка удаления несуществующего актива {device_id}: {e}')
        flash(request, 'Ошибка: Актив для удаления не найден.', 'danger')
    except DeletionError as e:
        logger.warning(f'Ошибка удаления актива {device_id} из-за зависимостей: {e}')
        flash(request, str(e), 'danger')
    except Exception as e:
        logger.error(f'Ошибка при удалении актива {device_id}: {e}', exc_info=True)
        flash(request, 'Произошла непредвиденная ошибка при удалении.', 'danger')
    return RedirectResponse(url=request.url_for('read_assets'), status_code=status.HTTP_303_SEE_OTHER)

@router.post('/assets/bulk-delete', name='bulk_delete_assets')
async def bulk_delete_assets(
    request: Request,
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service),
) -> Response:
    form_data = await request.form()
    device_ids = [int(id) for id in form_data.getlist('device_ids')]
    referer = request.headers.get('referer') or request.url_for('read_assets')
    if not device_ids:
        flash(request, 'Не выбрано ни одного актива для удаления.', 'warning')
        return RedirectResponse(referer, status_code=status.HTTP_303_SEE_OTHER)
    try:
        deleted_count, errors = await device_service.bulk_delete_devices(db=db, device_ids=device_ids, user_id=1)
        if deleted_count > 0:
            flash(request, f'Успешно удалено {deleted_count} активов.', 'success')
        if errors:
            error_message = 'Не удалось удалить некоторые активы: ' + ', '.join(errors)
            flash(request, error_message, 'danger')
    except Exception as e:
        logger.error(f'Ошибка при массовом удалении активов: {e}', exc_info=True)
        flash(request, f'Произошла ошибка при удалении: {e}', 'danger')
    return RedirectResponse(referer, status_code=status.HTTP_303_SEE_OTHER)

@router.post('/assets/bulk-update', name='bulk_update_assets')
async def bulk_update_assets(
    request: Request,
    device_ids_json: str = Form(..., alias='device_ids_json'),
    db: AsyncSession = Depends(get_db),
    device_service: DeviceService = Depends(get_device_service),
    status_id: int | None = Form(None),
    department_id: int | None = Form(None),
    location_id: int | None = Form(None),
) -> Response:
    referer = request.headers.get('referer') or request.url_for('read_assets')
    try:
        device_ids = json.loads(device_ids_json)
        if not isinstance(device_ids, list) or not device_ids:
            flash(request, 'Не выбрано ни одного актива для обновления.', 'warning')
            return RedirectResponse(referer, status_code=status.HTTP_303_SEE_OTHER)
        update_data = {'status_id': status_id, 'department_id': department_id, 'location_id': location_id}
        filtered_update_data = {k: v for k, v in update_data.items() if v is not None}
        if not filtered_update_data:
            flash(request, 'Не выбрано ни одного поля для обновления.', 'warning')
            return RedirectResponse(referer, status_code=status.HTTP_303_SEE_OTHER)
        updated_count = await device_service.bulk_update_devices(
            db=db, device_ids=device_ids, update_data=filtered_update_data, user_id=1
        )
        flash(request, f'Успешно обновлено {updated_count} активов.', 'success')
    except Exception as e:
        logger.error(f'Ошибка при массовом обновлении: {e}', exc_info=True)
        flash(request, f'Произошла ошибка при обновлении: {e}', 'danger')
    return RedirectResponse(referer, status_code=status.HTTP_303_SEE_OTHER)
