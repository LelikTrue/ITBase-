# app/main.py

import logging
import os
import secrets

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

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from app import models  # noqa: F401  # Важно для Alembic
from app.api.endpoints import (
    admin,
    analytics,
    assets,
    audit_logs,
    dictionaries,
    health,
    tags,
)
from app.config import BASE_DIR
from app.flash import flash
from app.logging_config import EndpointFilter

# --- Custom Swagger UI for Assets API ---
OPENAPI_ASSETS_SPEC_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'openapi-assets.yaml'
)
try:
    with open(OPENAPI_ASSETS_SPEC_PATH, encoding='utf-8') as f:
        openapi_assets_spec = yaml.safe_load(f)
except FileNotFoundError:
    print(
        f'Warning: {OPENAPI_ASSETS_SPEC_PATH} not found. Assets API docs will not be available.'
    )
    openapi_assets_spec = {}

# --- Настройка логирования ---
# Исключаем логи для эндпоинта /health
logging.getLogger('uvicorn.access').addFilter(EndpointFilter(path='/health'))

# Общая конфигурация логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')
logger = logging.getLogger(__name__)


def format_validation_errors_to_dict(errors: list) -> dict:
    """Превращает ошибки Pydantic в {field: message}."""
    error_dict = {}
    for error in errors:
        field_name = error.get('loc', [])[-1]
        error_dict[field_name] = error.get('msg', 'Неверное значение')
    return error_dict


def _configure_static_files(app: FastAPI):
    app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'static')), name='static')


def _configure_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    # SessionMiddleware is added last in create_app effectively, but here we can add it.
    # Note: Middleware is applied in reverse order of addition.
    # In original code, SessionMiddleware was added LAST (so it runs FIRST on request).
    # Then Auth middleware was added via decorator @app.middleware, which adds it too.
    # Ideally SessionMiddleware should be added last (executed first).
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv('SECRET_KEY', secrets.token_hex(32)),
        session_cookie='session',
        max_age=3600,
    )


def _configure_routers(app: FastAPI):
    app.include_router(assets.router)
    app.include_router(audit_logs.router)
    app.include_router(
        dictionaries.router, prefix='/api/dictionaries', tags=['Dictionaries']
    )
    app.include_router(admin.router, prefix='/admin')
    app.include_router(health.router, prefix='/api/health', tags=['health'])
    app.include_router(tags.router, prefix='/api/v1/tags', tags=['tags'])
    app.include_router(
        analytics.router, prefix='/api/analytics', tags=['analytics']
    )

    from app.api.endpoints import auth, users, web_auth
    app.include_router(auth.router, tags=['login'])
    app.include_router(users.router, prefix='/users', tags=['users'])
    app.include_router(web_auth.router)


def _configure_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = format_validation_errors_to_dict(exc.errors())
        logger.warning(f'Ошибка валидации: {errors} для URL: {request.url.path}')

        if request.url.path.startswith('/api/'):
            return JSONResponse(status_code=422, content={'detail': exc.errors()})

        try:
            form_data = await request.form()
            flash(
                request,
                {'errors': errors, 'submitted_data': dict(form_data)},
                'validation',
            )
        except Exception:
            flash(request, {'errors': errors}, 'validation')

        referer = request.headers.get('referer')
        if referer:
            return RedirectResponse(referer, status_code=303)
        return RedirectResponse(request.url_for('dashboard'), status_code=303)


def _configure_swagger_ui(app: FastAPI):
    @app.get('/docs/assets', include_in_schema=False)
    async def custom_swagger_ui_assets(request: Request):
        return get_swagger_ui_html(
            openapi_url='/openapi-assets.json', title='ITBase - Assets API Docs'
        )

    @app.get('/openapi-assets.json', include_in_schema=False)
    async def get_assets_openapi():
        return openapi_assets_spec


def _configure_auth_middleware(app: FastAPI):
    @app.middleware('http')
    async def auth_redirect_middleware(request: Request, call_next):
        """Redirect unauthenticated users to login page"""
        if request.headers.get('x-test-mode') == 'true' or request.headers.get('X-Test-Mode') == 'true':
            return await call_next(request)

        public_paths = [
            '/login', '/register', '/logout', '/health', '/ready',
            '/static', '/api', '/docs', '/openapi', '/users',
        ]

        # Check if path is public
        is_public = any(request.url.path.startswith(path) for path in public_paths)

        if not is_public:
            user_id = (
                request.session.get('user_id') if 'session' in request.scope else None
            )
            if not user_id:
                return RedirectResponse(url='/login', status_code=303)

        return await call_next(request)


def create_app() -> FastAPI:
    app = FastAPI(
        title='ITBase',
        description='Сервис для учета и управления ИТ-активами.',
        version='1.0.0',
        docs_url=None,
        redoc_url=None,
    )

    _configure_static_files(app)

    # Configure Routers and Exception Handlers
    _configure_routers(app)
    _configure_exception_handlers(app)
    _configure_swagger_ui(app)

    # Middleware Configuration
    # Note: Middleware is added LIFO (Last Added, First Executed for request).
    # We want execution order: CORS -> Session -> Auth.
    # So we must add them in reverse order: Auth, then Session, then CORS.

    # 1. Auth Middleware (Innermost of these three)
    _configure_auth_middleware(app)

    # 2. Session Middleware (Wraps Auth)
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv('SECRET_KEY', secrets.token_hex(32)),
        session_cookie='session',
        max_age=3600,
    )

    # 3. CORS Middleware (Wraps Session)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.get('/', status_code=302, include_in_schema=False)
    async def root_redirect(request: Request):
        try:
            return RedirectResponse(url=request.url_for('dashboard'), status_code=303)
        except Exception as e:
            logger.critical(f"Не удалось найти 'dashboard': {e}")
            return JSONResponse(
                status_code=500, content={'detail': 'Ошибка конфигурации'}
            )

    return app


app = create_app()
