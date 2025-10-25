# app/main.py

import logging
import os
import secrets
from typing import Any

import yaml

# Условный импорт для разработки
if os.getenv('APP_MODE') == 'dev':
    try:
        import pretty_errors
        pretty_errors.configure(
            separator_character='*',
            line_number_first=True,
            display_locals=True,
            filename_display=pretty_errors.FILENAME_EXTENDED,
        )
        print('INFO:     pretty_errors is enabled for development.')
    except ImportError:
        print("WARNING:  'pretty_errors' is not installed, skipping.")

from fastapi import FastAPI, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

# --- НОВЫЕ ИМПОРТЫ ДЛЯ HEALTH CHECK ---
from sqlalchemy import text
from app.db.database import AsyncSessionFactory

import app.models  # Важно для Alembic
from app.api.endpoints import admin, assets, audit_logs, dictionaries, health, tags
from app.config import BASE_DIR
from app.flash import flash

# --- Custom Swagger UI for Assets API ---
OPENAPI_ASSETS_SPEC_PATH = os.path.join(os.path.dirname(__file__), '..', 'openapi-assets.yaml')
try:
    with open(OPENAPI_ASSETS_SPEC_PATH, encoding='utf-8') as f:
        openapi_assets_spec = yaml.safe_load(f)
except FileNotFoundError:
    print(f'Warning: {OPENAPI_ASSETS_SPEC_PATH} not found. Assets API docs will not be available.')
    openapi_assets_spec = {}

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_validation_errors_to_dict(errors: list) -> dict:
    """Превращает ошибки Pydantic в {field: message}."""
    error_dict = {}
    for error in errors:
        field_name = error.get('loc', [])[-1]
        error_dict[field_name] = error.get('msg', 'Неверное значение')
    return error_dict

def create_app() -> FastAPI:
    app = FastAPI(
        title='ITBase',
        description='Сервис для учета и управления ИТ-активами.',
        version='1.0.0',
        docs_url=None,
        redoc_url=None,
    )

    app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'static')), name='static')

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv('SECRET_KEY', secrets.token_hex(32)),
        session_cookie='session',
        max_age=3600
    )

    # --- ПОДКЛЮЧЕНИЕ РОУТЕРОВ ---
    app.include_router(assets.router)
    app.include_router(audit_logs.router)
    app.include_router(dictionaries.router)
    app.include_router(admin.router, prefix='/admin')
    #app.include_router(health.router, prefix='/api/health', tags=['health'])
    app.include_router(tags.router, prefix='/api/v1/tags', tags=['tags'])

    # --- НОВЫЙ HEALTH CHECK БЕЗ ПРОВЕРКИ БД ---
    @app.get('/health', include_in_schema=False)
    async def health_check():
        """
        Простая проверка работоспособности сервиса (liveness probe).
        Отвечает OK, если веб-сервер запущен. НЕ проверяет базу данных.
        """
        return {'status': 'ok'}

    @app.get('/ready', include_in_schema=False)
    async def readiness_check():
        """Для Kubernetes readiness probe."""
        try:
            async with AsyncSessionFactory() as db:
                await db.execute(text("SELECT 1"))
            return {'status': 'ready', 'database': 'ok'}
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return JSONResponse(status_code=503, content={'status': 'not ready'})

    # --- Обработчики ошибок ---
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = format_validation_errors_to_dict(exc.errors())
        logger.warning(f'Ошибка валидации: {errors} для URL: {request.url.path}')

        if request.url.path.startswith('/api/'):
            return JSONResponse(status_code=422, content={'detail': exc.errors()})

        try:
            form_data = await request.form()
            flash(request, {'errors': errors, 'submitted_data': dict(form_data)}, 'validation')
        except Exception:
            flash(request, {'errors': errors}, 'validation')

        referer = request.headers.get('referer')
        if referer:
            return RedirectResponse(referer, status_code=303)
        return RedirectResponse(request.url_for('dashboard'), status_code=303)

    # --- Swagger для активов ---
    @app.get('/docs/assets', include_in_schema=False)
    async def custom_swagger_ui_assets(request: Request):
        return get_swagger_ui_html(
            openapi_url='/openapi-assets.json',
            title='ITBase - Assets API Docs'
        )

    @app.get('/openapi-assets.json', include_in_schema=False)
    async def get_openapi_assets_endpoint():
        return openapi_assets_spec

    @app.get('/', status_code=302, include_in_schema=False)
    async def root_redirect(request: Request):
        try:
            return RedirectResponse(url=request.url_for('dashboard'), status_code=303)
        except Exception as e:
            logger.critical(f"Не удалось найти 'dashboard': {e}")
            return JSONResponse(status_code=500, content={"detail": "Ошибка конфигурации"})

    return app

# Глобальный экземпляр
app = create_app()