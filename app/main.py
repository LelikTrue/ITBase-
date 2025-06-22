from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
import os
import secrets

from app.db.database import engine, Base, get_db
import app.models  # Важно для Alembic
from app.api.endpoints import assets
from app.config import TEMPLATES_DIR

# Инициализируем Jinja2Templates
print(f"Templates directory: {TEMPLATES_DIR}")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Событие запуска приложения (lifespan для FastAPI 0.100.0+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup initiated.")
    yield
    print("Application shutdown complete.")

app = FastAPI(lifespan=lifespan, title="IT Asset Management API")

# Подключение статических файлов (CSS, JS, изображения)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка сессий
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", secrets.token_hex(32)),
    session_cookie="session",
    max_age=3600  # 1 час
)

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