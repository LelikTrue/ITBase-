# app/main.py

import logging
import os
import secrets
import yaml
from typing import Any, Dict

# Условный импорт для разработки.
# pretty_errors будет импортирован только если APP_MODE=dev.
if os.getenv("APP_MODE") == "dev":
    try:
        import pretty_errors
        pretty_errors.configure(
            separator_character='*',
            line_number_first=True,
            display_locals=True,
            filename_display=pretty_errors.FILENAME_EXTENDED,
        )
        print("INFO:     pretty_errors is enabled for development.")
    except ImportError:
        print("WARNING:  'pretty_errors' is not installed, skipping.")

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

import app.models  # Важно для Alembic
from app.api.endpoints import admin, assets, audit_logs, dictionaries, health, tags
from app.config import BASE_DIR
from app.flash import flash

# --- Custom Swagger UI for Assets API ---
# Загружаем спецификацию OpenAPI для активов
OPENAPI_ASSETS_SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "openapi-assets.yaml")
try:
    with open(OPENAPI_ASSETS_SPEC_PATH, "r", encoding="utf-8") as f:
        openapi_assets_spec = yaml.safe_load(f)
except FileNotFoundError:
    print(f"Warning: {OPENAPI_ASSETS_SPEC_PATH} not found. Assets API docs will not be available.")
    openapi_assets_spec = {}

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_validation_errors_to_dict(errors: list) -> dict:
    """Превращает список ошибок Pydantic в словарь {field: message}."""
    error_dict = {}
    for error in errors:
        # Pydantic возвращает 'loc' как кортеж, например ('body', 'employee_id')
        field_name = error.get("loc", [])[-1]
        error_dict[field_name] = error.get("msg", "Неверное значение")
    return error_dict

def create_app() -> FastAPI:
    """
    Фабрика для создания экземпляра приложения FastAPI.
    """
    app = FastAPI(
        title="ITBase",
        description="Сервис для учета и управления ИТ-активами.",
        version="1.0.0",
        docs_url=None,  # Отключаем стандартные /docs
        redoc_url=None,  # Отключаем стандартные /redoc
    )

    # Подключение статических файлов (CSS, JS, изображения)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

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

    # ===============================================================
    #  ПОДКЛЮЧЕНИЕ РОУТЕРОВ (ПРАВИЛЬНЫЙ ПОРЯДОК)
    # ===============================================================

    # 1. Сначала самые конкретные и уникальные пути.
    # Эти пути не могут быть случайно перехвачены другими роутерами.
    app.include_router(assets.router)
    app.include_router(audit_logs.router)

    # 2. Затем роутеры с "жадными" путями (`/{slug}`).
    # Они подключаются ПОСЛЕ конкретных, чтобы не перехватывать их.
    app.include_router(dictionaries.router)
    app.include_router(admin.router, prefix="/admin") # Префикс изолирует все его пути

    # 3. В самом конце - чисто API-роутеры с префиксами.
    # Префиксы /api/ делают их полностью изолированными.
    app.include_router(health.router, prefix="/api/health", tags=["health"])
    app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])

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

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Перехватывает ошибки валидации.
        - Для API-запросов (/api/*) возвращает JSON с ошибкой 422.
        - Для обычных веб-форм делает редирект назад с flash-сообщением.
        """
        # 1. Форматируем ошибки в удобный словарь
        errors = format_validation_errors_to_dict(exc.errors())
        logger.warning(f"Ошибка валидации: {errors} для URL: {request.url.path}")

        # 2. Проверяем, является ли это API-запросом
        if request.url.path.startswith("/api/"):
            # Если да, возвращаем стандартный JSON-ответ
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": exc.errors()}
            )

        # 3. Если это не API, то это веб-форма. Работаем как раньше.
        try:
            # Пытаемся получить данные формы.
            form_data = await request.form()
            # Кладем в сессию и ошибки, и данные формы
            flash(request, {"errors": errors, "submitted_data": dict(form_data)}, "validation")
        except Exception:
            # Если не удалось прочитать форму, просто покажем ошибку
            flash(request, {"errors": errors}, "validation")

        # 4. Возвращаем пользователя на ту страницу, с которой он пришел
        referer = request.headers.get("referer")
        if referer:
            return RedirectResponse(referer, status_code=303)

        # Запасной вариант, если referer не найден
        return RedirectResponse(request.url_for("dashboard"), status_code=303)

    @app.get("/docs/assets", include_in_schema=False)
    async def custom_swagger_ui_assets(request: Request):
        """Отображает кастомную Swagger UI для API активов."""
        return get_swagger_ui_html(
            openapi_url="/openapi-assets.json",
            title="ITBase - Assets API Docs"
        )

    @app.get("/openapi-assets.json", include_in_schema=False)
    async def get_openapi_assets_endpoint():
        """Предоставляет спецификацию OpenAPI для API активов."""
        return openapi_assets_spec

    @app.get("/", status_code=302, include_in_schema=False)
    async def root_redirect(request: Request):
        """
        Перенаправляет с корневого URL на страницу дашборда.
        """
        # Используем url_for для динамического получения URL.
        # Код 303 See Other - более корректный для редиректа после действия.
        return RedirectResponse(url=request.url_for("dashboard"), status_code=status.HTTP_303_SEE_OTHER)

    return app

# Создаем глобальный экземпляр для запуска через Uvicorn
app = create_app()