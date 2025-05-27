# app/main.py
from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.db.database import engine, Base, get_db
import app.models # Важно: Импортируем модуль app.models, чтобы Base.metadata его увидел для Alembic

# Импортируем эндпоинты
from app.api.endpoints import assets

# Настройки Jinja2 шаблонов
# Используем абсолютный путь, чтобы избежать проблем с поиском
templates = Jinja2Templates(directory="/app/templates")

# Событие запуска приложения (lifespan для FastAPI 0.100.0+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup initiated.")
    yield
    print("Application shutdown complete.")

app = FastAPI(lifespan=lifespan, title="IT Asset Management API")

# Включаем роутер для активов/устройств
# Роуты из assets.py будут доступны по их прямому пути (например, /dashboard, /add)
# Если вы захотите добавить API-префикс, например /api/v1, то измените здесь
app.include_router(assets.router)

# Корневой эндпоинт, который перенаправляет на страницу дашборда
@app.get("/", response_class=RedirectResponse, status_code=302)
async def root_redirect(request: Request):
    """
    Перенаправляет с корневого URL на страницу дашборда.
    """
    # Теперь 'read_assets' - это имя роута в assets.py, который находится по пути /dashboard
    return request.url_for("read_assets")