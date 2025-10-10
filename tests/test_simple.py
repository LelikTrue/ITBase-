# Файл: tests/test_simple.py

import pytest
from httpx import AsyncClient

# Помечаем все тесты в этом файле как асинхронные
pytestmark = pytest.mark.asyncio


async def test_single_endpoint_with_db_access(async_client: AsyncClient):
    """
    Единственный, изолированный тест для проверки эндпоинта,
    который гарантированно обращается к базе данных.
    
    Цель: доказать, что наша конфигурация фикстур (conftest.py) работает правильно.
    """
    # Предполагается, что роутер health.py подключен с префиксом /api/health
    response = await async_client.get("/api/health/ready")
    
    assert response.status_code == 200
    assert response.json() == {"db_status": "ok"}