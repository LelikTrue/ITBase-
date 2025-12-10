import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department, DeviceStatus, Employee, Location, Manufacturer, Tag

pytestmark = pytest.mark.asyncio


# Parameterized test for simple dictionaries
@pytest.mark.parametrize(
    "dict_name, payload, model_class",
    [
        ("locations", {"name": "New Loc", "slug": "new-loc"}, Location),
        ("departments", {"name": "New Dept", "slug": "new-dept"}, Department),
        ("device-statuses", {"name": "New Status", "slug": "new-status"}, DeviceStatus),
        ("manufacturers", {"name": "New Maker"}, Manufacturer),  # No slug
        ("tags", {"name": "New Tag"}, Tag),  # No slug
    ]
)
async def test_generic_dictionary_crud(
    async_client: AsyncClient,
    db_session: AsyncSession,
    dict_name,
    payload,
    model_class
):
    """Тест: CRUD для простых справочников."""
    base_url = f'/api/dictionaries/{dict_name}'

    # 1. CREATE
    response = await async_client.post(base_url, data=payload)
    assert response.status_code == 201
    created_id = response.json()['id']

    # Verify in DB
    item = await db_session.get(model_class, created_id)
    assert item is not None
    assert item.name == payload['name']

    # 2. READ (List)
    response = await async_client.get(base_url)
    assert response.status_code == 200
    data = response.json()
    assert any(d['id'] == created_id for d in data)

    # UPDATE
    # Use full payload with updated name to satisfy Schema validation (e.g. required slug)
    update_payload = payload.copy()
    update_payload["name"] = f"{payload['name']} Updated"
    response = await async_client.put(f'{base_url}/{created_id}', json=update_payload)
    assert response.status_code == 200

    # Expunge to ensure DELETE fetches fresh object with options (avoiding MissingGreenlet on lazy load)
    db_session.expunge_all()

    # 3. DELETE
    response = await async_client.delete(f'{base_url}/{created_id}')
    assert response.status_code == 204

    # Verify deletion
    item = await db_session.get(model_class, created_id)
    assert item is None


async def test_employee_crud(async_client: AsyncClient, db_session: AsyncSession):
    """Тест: CRUD для Сотрудников (специфичные поля)."""
    dict_name = "employees"
    base_url = f'/api/dictionaries/{dict_name}'
    payload = {
        "last_name": "Petrov",
        "first_name": "Petr",
        "patronymic": "Petrovich",
        "email": "petr@test.com"
    }

    # CREATE
    response = await async_client.post(base_url, data=payload)
    assert response.status_code == 201
    created_id = response.json()['id']

    # Verify DB
    emp = await db_session.get(Employee, created_id)
    assert emp.last_name == "Petrov"
    assert emp.first_name == "Petr"

    # DUPLICATE CHECK (Email unique)
    response = await async_client.post(base_url, data=payload)
    assert response.status_code == 409
    assert "уже существует" in response.json()['detail']


async def test_dictionary_duplicate_error(
    async_client: AsyncClient, db_session: AsyncSession
):
    """Тест: Создание дубликата (slug) возвращает 409."""
    dict_name = "locations"
    base_url = f'/api/dictionaries/{dict_name}'
    payload = {"name": "Unique Loc", "slug": "unique-loc"}

    # First create
    await async_client.post(base_url, data=payload)

    # Second create
    response = await async_client.post(base_url, data=payload)
    assert response.status_code == 409
    detail = response.json()['detail']
    assert "уже существует" in detail or "Unique" in detail


async def test_get_models_by_manufacturer(
    async_client: AsyncClient,
    test_data: dict,
    db_session: AsyncSession
):
    """Тест: Получение моделей по производителю."""
    manufacturer = test_data['manufacturer']

    # Add another model for this manufacturer
    from app.models import DeviceModel
    model2 = DeviceModel(
        name="Model 2",
        manufacturer_id=manufacturer.id,
        asset_type_id=test_data['asset_type'].id
    )
    db_session.add(model2)
    # Ensure flush to get IDs, but commit not needed due to session fixture
    await db_session.flush()

    response = await async_client.get(f'/api/dictionaries/api/models/by-manufacturer/{manufacturer.id}')
    assert response.status_code == 200
    data = response.json()

    assert len(data) >= 1
    # Check if we can find our models.
    # Note: test_data might create "TestModel 9000"
    names = [m['name'] for m in data]
    assert "Model 2" in names
