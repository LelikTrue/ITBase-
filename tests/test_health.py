# tests/test_health.py

import pytest
from httpx import AsyncClient

# Помечаем все тесты в этом файле как асинхронные
pytestmark = pytest.mark.asyncio


async def test_api_health(async_client: AsyncClient):
    """
    Тест: Проверяем базовый эндпоинт /api/health/health.
    Он не лезет в базу, просто отвечает, что API жив.
    """
    response = await async_client.get("/api/health/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_api_health_ready(async_client: AsyncClient):
    """
    Тест: Проверяем эндпоинт /api/health/ready, который ОБЯЗАН проверить подключение к БД.
    """
    response = await async_client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.json() == {"db_status": "ok"}
