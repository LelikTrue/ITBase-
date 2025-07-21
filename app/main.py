from fastapi import FastAPI, Request, Depends

from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from app.templating import templates
import logging
import os
import secrets
import json
from pathlib import Path
from typing import Dict, Any, List

from app.db.database import Base, get_db
from app.db.database import SessionLocal
import app.models  # Важно для Alembic, не удалять
from app.api.endpoints import assets, action_logs, health, dictionaries, admin
from app.models.asset_type import AssetType # Предполагаем, что модель находится здесь

def load_admin_sections() -> List[Dict[str, str]]:
    """Загружает конфигурацию разделов админ-панели из JSON-файла."""
    # Проверяем оба возможных расположения файла
    config_paths = [
        Path(__file__).parent.parent / 'admin_sections.json',  # В корне проекта
        Path(__file__).parent / 'config' / 'admin_sections.json'  # В папке app/config/
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('sections', [])
            except Exception as e:
                logger.error(f"Ошибка при загрузке {config_path}: {e}")
    
    logger.warning("Файл конфигурации разделов админ-панели не найден")
    return []

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def seed_initial_data():
    """Заполняет базу начальными данными из JSON-файлов, если таблицы пусты."""
    db = SessionLocal()
    try:
        # Проверяем, нужно ли заполнять таблицу asset_types
        if db.query(AssetType).count() == 0:
            logger.info("Таблица 'asset_types' пуста. Заполняем начальными данными...")
            file_path = Path(__file__).parent.parent / 'initdb' / 'asset_types.json'
            
            if not file_path.exists():
                logger.warning(f"Файл {file_path} не найден. Пропускаем заполнение.")
                return

            # Читаем файл с явным указанием кодировки utf-8-sig, 
            # которая корректно обрабатывает BOM (метку порядка байтов), часто добавляемую редакторами в Windows.
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                asset_types_data = json.load(f)
            
            for item_data in asset_types_data:
                db_item = AssetType(**item_data)
                db.add(db_item)
            
            db.commit()
            logger.info("Таблица 'asset_types' успешно заполнена.")
    finally:
        db.close()

# Событие запуска приложения (lifespan для FastAPI 0.100.0+)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup initiated.")
    seed_initial_data()
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

# Включаем роутеры
app.include_router(assets.router)
app.include_router(action_logs.router, prefix="/admin", tags=["admin", "audit"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(dictionaries.router, prefix="/admin")
app.include_router(admin.router, prefix="/admin")

# Эндпоинты для проверки работоспособности
@app.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, Any]:
    """
    Проверка работоспособности сервиса (для Kubernetes liveness probe).
    """
    return {"status": "ok", "service": "it-asset-management"}

@app.get("/ready", include_in_schema=False)
async def readiness_check() -> Dict[str, Any]:
    """
    Проверка готовности сервиса (для Kubernetes readiness probe).
    """
    return {"status": "ready", "service": "it-asset-management"}

# Глобальные обработчики ошибок
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Корневой эндпоинт, который перенаправляет на страницу дашборда
@app.get("/", status_code=302)
async def root_redirect(request: Request):
    """
    Перенаправляет с корневого URL на страницу дашборда.
    """
    return RedirectResponse(request.url_for("dashboard"))

# Главная страница админ-панели
@app.get("/admin", name="admin_dashboard", include_in_schema=False)
async def admin_dashboard(request: Request):
    """Отображает главную страницу панели администрирования."""
    try:
        sections = load_admin_sections()
        logger.info(f"Загружены разделы админ-панели: {sections}")
        
        # Проверяем, что все необходимые поля есть в каждом разделе
        valid_sections = []
        for section in sections:
            if all(key in section for key in ['title', 'description', 'icon', 'endpoint']):
                valid_sections.append(section)
            else:
                logger.warning(f"Пропущен раздел из-за неполных данных: {section}")
        
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "admin_sections": valid_sections,
                "debug": True  # Включаем отладочный режим
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке админ-панели: {str(e)}", exc_info=True)
        raise