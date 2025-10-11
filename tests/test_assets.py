import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AssetType, Device, DeviceModel, DeviceStatus, Manufacturer

pytestmark = pytest.mark.asyncio


async def create_test_dependencies(db: AsyncSession):
    """Создает и сохраняет в БД необходимые для тестов записи в справочниках."""
    asset_type = AssetType(name='Компьютер', prefix='PC')
    manufacturer = Manufacturer(name='TestCorp')
    device_status = DeviceStatus(name='Активен')

    db.add_all([asset_type, manufacturer, device_status])
    await db.flush()

    device_model = DeviceModel(name='TestModel 9000', manufacturer_id=manufacturer.id, asset_type_id=asset_type.id)
    db.add(device_model)
    await db.flush()

    return {
        'asset_type_id': asset_type.id,
        'manufacturer_id': manufacturer.id,
        'status_id': device_status.id,
        'device_model_id': device_model.id
    }


async def test_read_assets_list_empty(async_client: AsyncClient):
    """Тест: Страница списка активов открывается, даже если активов нет."""
    response = await async_client.get('/assets-list')
    assert response.status_code == 200
    assert 'Добавить актив' in response.text # Проверяем, что кнопка есть


async def test_read_assets_list_with_data(async_client: AsyncClient, db_session: AsyncSession):
    """Тест: Страница списка активов правильно отображает существующий актив."""
    deps = await create_test_dependencies(db_session)
    test_asset = Device(
        name='Test PC 01', inventory_number='INV-01',
        asset_type_id=deps['asset_type_id'], device_model_id=deps['device_model_id'],
        status_id=deps['status_id']
    )
    db_session.add(test_asset)
    await db_session.flush()

    response = await async_client.get('/assets-list')
    assert response.status_code == 200
    assert 'Инвентарный номер' in response.text
    assert 'INV-01' in response.text


async def test_full_asset_crud_cycle(async_client: AsyncClient, db_session: AsyncSession):
    """Тест: Проверяем полный жизненный цикл актива."""
    deps = await create_test_dependencies(db_session)

    # CREATE
    asset_data = {
        'name': 'Тестовый ПК для CRUD', 'inventory_number': 'TEST-CRUD-001',
        'asset_type_id': deps['asset_type_id'],
        'device_model_id': deps['device_model_id'],
        'status_id': deps['status_id'],
    }
    create_response = await async_client.post('/create', data=asset_data, follow_redirects=True)
    assert create_response.status_code == 200
    assert 'Актив успешно добавлен' in create_response.text

    stmt = select(Device).where(Device.inventory_number == 'TEST-CRUD-001')
    created_device = (await db_session.execute(stmt)).scalar_one()
    device_id = created_device.id

    # READ
    edit_page_response = await async_client.get(f'/edit/{device_id}')
    assert edit_page_response.status_code == 200

    # UPDATE
    update_data = {
        'name': 'Обновленный ПК', 'inventory_number': 'TEST-CRUD-001-UPDATED',
        'asset_type_id': deps['asset_type_id'],
        'device_model_id': deps['device_model_id'],
        'status_id': deps['status_id'],
    }
    await async_client.post(f'/update/{device_id}', data=update_data, follow_redirects=True)

    await db_session.refresh(created_device)
    assert created_device.inventory_number == 'TEST-CRUD-001-UPDATED'

    # DELETE
    await async_client.post(f'/delete/{device_id}', follow_redirects=True)

    deleted_device = await db_session.get(Device, device_id)
    assert deleted_device is None
