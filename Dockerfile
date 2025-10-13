# ===== БАЗОВЫЙ ОБРАЗ =====
FROM python:3.12.3-slim-bookworm AS base

# Установка системных зависимостей
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем зависимости
WORKDIR /build
COPY requirements requirements/

# ===== СТАДИЯ СОБРАННЫХ ЗАВИСИМОСТЕЙ =====
FROM base AS deps

# Устанавливаем зависимости с кешированием
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt

# ===== РАЗРАБОТКА =====
FROM base AS dev

# Устанавливаем зависимости разработки
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/dev.txt && \
    pip install --no-cache-dir pytest pytest-cov

# Копируем исходный код
WORKDIR /app
COPY --chown=1000:1000 . .

# Настройка пользователя
RUN useradd -u 1000 -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Порт для разработки
EXPOSE 8000

# Команда по умолчанию
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== ПРОДУКЦИЯ =====
FROM base AS prod

# Устанавливаем только runtime зависимости
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости из стадии deps
COPY --from=deps /opt/venv /opt/venv

# Устанавливаем production зависимости
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements/prod.txt

# Копируем исходный код
WORKDIR /app
COPY --chown=1000:1000 . .

# Создаем пользователя
RUN useradd -u 1000 -m appuser && \
    chown -R appuser:appuser /app

# Настройка окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH=/app

# Создаем необходимые директории
RUN mkdir -p /app/static /app/media /app/logs && \
    chown -R appuser:appuser /app/static /app/media /app/logs

# Переключаемся на непривилегированного пользователя
USER appuser

# Открываем порт
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда запуска
CMD ["/bin/sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers $(( $(nproc) * 2 + 1 )) --worker-connections 1000 --timeout 60 --keep-alive 5 --access-logfile - --error-logfile - --log-level info --worker-tmp-dir /dev/shm"]
