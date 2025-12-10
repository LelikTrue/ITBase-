import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionLog
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.device_service import DeviceService
from app.services.exceptions import DuplicateDeviceError

pytestmark = pytest.mark.asyncio


async def test_create_device_success(db_session: AsyncSession, test_data: dict):
    service = DeviceService()
    user_id = test_data['user'].id
    unique_serial = f"SN-{uuid.uuid4()}"

    asset_data = AssetCreate(
        name="New Device",
        serial_number=unique_serial,
        asset_type_id=test_data['asset_type'].id,
        device_model_id=test_data['device_model'].id,
        status_id=test_data['status'].id,
        manufacturer_id=test_data['manufacturer'].id,
        tag_ids=[test_data['tag'].id]
    )

    device = await service.create_device(db_session, asset_data, user_id)

    assert device.id is not None
    assert device.name == "New Device"
    assert device.inventory_number.startswith("PC-")
    assert len(device.tags) == 1
    assert device.tags[0].id == test_data['tag'].id

    # Check Audit Log
    stmt = select(ActionLog).where(ActionLog.entity_id == device.id)
    log = (await db_session.execute(stmt)).scalar_one()
    assert log.action_type == "create"


async def test_create_device_duplicate_serial(db_session: AsyncSession, test_data: dict):
    service = DeviceService()
    user_id = test_data['user'].id
    unique_serial = f"SN-{uuid.uuid4()}"

    # Create first device
    asset_data1 = AssetCreate(
        name="Device 1",
        serial_number=unique_serial,
        asset_type_id=test_data['asset_type'].id,
        device_model_id=test_data['device_model'].id,
        status_id=test_data['status'].id,
        manufacturer_id=test_data['manufacturer'].id
    )
    await service.create_device(db_session, asset_data1, user_id)

    # Try to create second with same serial
    asset_data2 = AssetCreate(
        name="Device 2",
        serial_number=unique_serial,
        asset_type_id=test_data['asset_type'].id,
        device_model_id=test_data['device_model'].id,
        status_id=test_data['status'].id,
        manufacturer_id=test_data['manufacturer'].id
    )

    with pytest.raises(DuplicateDeviceError) as exc:
        await service.create_device(db_session, asset_data2, user_id)

    # "уже существует" is generic part of message or explicit check
    assert "уже существует" in str(exc.value)


async def test_get_devices_with_filters(db_session: AsyncSession, test_data: dict):
    service = DeviceService()
    user_id = test_data['user'].id

    # Create devices with different attributes
    for i in range(3):
        await service.create_device(
            db_session,
            AssetCreate(
                name=f"FilterDevice {i}",
                serial_number=f"SN-{uuid.uuid4()}",
                asset_type_id=test_data['asset_type'].id,
                device_model_id=test_data['device_model'].id,
                status_id=test_data['status'].id,
                manufacturer_id=test_data['manufacturer'].id,
                location_id=test_data['location'].id if i == 0 else None
            ),
            user_id
        )

    # Filter by name
    devices, total = await service.get_devices_with_filters(
        db_session, page=1, page_size=10, search="FilterDevice 1"
    )
    assert total == 1
    assert devices[0].name == "FilterDevice 1"

    # Filter by location
    devices, total = await service.get_devices_with_filters(
        db_session, page=1, page_size=10, location_id=test_data['location'].id
    )
    # Note: test_data might be used by other tests if scope was larger, but function scope ensures clean-ish state
    # BUT wait, test_data fixture creates objects. If we create devices linking to them,
    # count depends on how many point to it.
    # In this function, we created 1 device with location.
    # If other tests created devices, they are rolled back.
    # BUT checking "FilterDevice 0" name ensures we found OURS.
    assert len(devices) >= 1
    names = [d.name for d in devices]
    assert "FilterDevice 0" in names

    # Filter by non-existent
    devices, total = await service.get_devices_with_filters(
        db_session, page=1, page_size=10, search="NonExistent"
    )
    assert total == 0


async def test_update_device_success(db_session: AsyncSession, test_data: dict):
    service = DeviceService()
    user_id = test_data['user'].id
    unique_serial = f"SN-{uuid.uuid4()}"

    device = await service.create_device(
        db_session,
        AssetCreate(
            name="Original Name",
            serial_number=unique_serial,
            asset_type_id=test_data['asset_type'].id,
            device_model_id=test_data['device_model'].id,
            status_id=test_data['status'].id,
            manufacturer_id=test_data['manufacturer'].id
        ),
        user_id
    )

    # Update
    update_data = AssetUpdate(
        name="Updated Name",
        location_id=test_data['location'].id
    )
    updated_device = await service.update_device_with_audit(
        db_session, device.id, update_data, user_id
    )

    assert updated_device.name == "Updated Name"
    assert updated_device.location_id == test_data['location'].id

    # Check Audit Log
    stmt = select(ActionLog).where(ActionLog.entity_id == device.id, ActionLog.action_type == "update")
    log = (await db_session.execute(stmt)).scalar_one()
    assert log.details['changes']['name']['old'] == "Original Name"
    assert log.details['changes']['name']['new'] == "Updated Name"


async def test_delete_device(db_session: AsyncSession, test_data: dict):
    service = DeviceService()
    user_id = test_data['user'].id
    unique_serial = f"SN-{uuid.uuid4()}"

    device = await service.create_device(
        db_session,
        AssetCreate(
            name="To Delete",
            serial_number=unique_serial,
            asset_type_id=test_data['asset_type'].id,
            device_model_id=test_data['device_model'].id,
            status_id=test_data['status'].id,
            manufacturer_id=test_data['manufacturer'].id
        ),
        user_id
    )

    # Delete
    await service.delete_device_with_audit(db_session, device.id, user_id)

    # Verify deletion
    assert await service.get_device_with_relations(db_session, device.id) is None

    # Check Audit Log
    stmt = select(ActionLog).where(ActionLog.entity_id == device.id, ActionLog.action_type == "delete")
    log = (await db_session.execute(stmt)).scalar_one()
    # Depending on implementation, details might have name or full dump
    assert log.details.get('name') == "To Delete" or "To Delete" in str(log.details)


async def test_bulk_update(db_session: AsyncSession, test_data: dict):
    service = DeviceService()
    user_id = test_data['user'].id

    # Create 2 devices
    id_list = []
    for i in range(2):
        d = await service.create_device(
            db_session,
            AssetCreate(
                name=f"Bulk {i}",
                serial_number=f"SN-{uuid.uuid4()}",
                asset_type_id=test_data['asset_type'].id,
                device_model_id=test_data['device_model'].id,
                status_id=test_data['status'].id,
                manufacturer_id=test_data['manufacturer'].id
            ),
            user_id
        )
        id_list.append(d.id)

    update_data = {"location_id": test_data['location'].id}
    count = await service.bulk_update_devices(db_session, id_list, update_data, user_id)

    assert count == 2

    # Verify update
    for dev_id in id_list:
        d = await service.get_device_with_relations(db_session, dev_id)
        assert d.location_id == test_data['location'].id
