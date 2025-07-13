from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
import logging
import os
import secrets
from typing import Dict, Any

from app.db.database import Base, get_db
import app.models  # Важно для Alembic
from app.api.endpoints import assets, audit_logs, health, dictionaries, admin

# Настройка базового логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# Включаем роутеры
app.include_router(assets.router)
app.include_router(audit_logs.router, prefix="/api/audit", tags=["audit"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(dictionaries.router)
app.include_router(admin.router)

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
    return RedirectResponse(request.url_for("read_assets"))