# app/main.py
from fastapi import FastAPI, Depends, Request, RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from app.db.database import engine, Base, get_db # Убедитесь, что engine и Base необходимы здесь
from sqlalchemy import func

# Важно: Импортируйте все ваши модели, чтобы Base.metadata их увидел
# Это нужно для Alembic, чтобы знать, какие таблицы управлять/генерировать миграции
import app.models
# from app.models.asset import Device, AssetType, DeviceStatus, DeviceModel, Department, Location, Employee, Manufacturer # Уточненный импорт. Не обязательно импортировать здесь, если модели используются только в роутах.

# Импортируем эндпоинты
from app.api.endpoints import assets

# Настройки Jinja2 шаблонов
templates = Jinja2Templates(directory="templates")

# Событие запуска приложения (lifespan для FastAPI 0.100.0+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup initiated.")
    yield
    print("Application shutdown complete.")


app = FastAPI(lifespan=lifespan, title="IT Asset Management API")

# Включаем роутер для активов/устройств
# Убедитесь, что base_url для url_for в шаблонах корректен, если вы добавите prefix="/api"
app.include_router(assets.router) # Оставляем без prefix="/api", чтобы UI роуты были доступны напрямую

# Корневой эндпоинт, который перенаправляет на страницу дашборда
@app.get("/", response_class=RedirectResponse, status_code=302)
async def root_redirect(request: Request):
    """
    Перенаправляет с корневого URL на страницу дашборда.
    """
    return request.url_for("read_assets") # Используем url_for по имени роута из assets.py

# УДАЛЕННЫЙ ЭНДПОИНТ:
# Эндпоинт для отображения дашборда был удален из main.py,
# так как он теперь определен в app/api/endpoints/assets.py под именем 'read_assets'.
# @app.get("/dashboard", response_class=HTMLResponse, name="dashboard")
# async def dashboard(request: Request, db: Session = Depends(get_db)):
#     # ... (логика дашборда, которая теперь находится в assets.py) ...
#     pass