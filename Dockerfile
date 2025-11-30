# =====================================================================
# Стадия 1: builder-base – Установка основных зависимостей
# =====================================================================
# Используем плавающий тег для получения последних обновлений безопасности
FROM python:3.12-slim-bookworm AS builder-base

# Устанавливаем системные переменные
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Обновляем списки пакетов, обновляем систему и устанавливаем curl/git
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы зависимостей
COPY setup.py README.md ./
COPY requirements/base.txt requirements/dev.txt requirements/prod.txt ./requirements/

# Устанавливаем ТОЛЬКО основные зависимости
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --user --no-cache-dir -r requirements/base.txt

# =====================================================================
# Стадия 2: dev-dependencies – Установка dev-зависимостей
# =====================================================================
FROM builder-base AS dev-dependencies

# Доустанавливаем dev-зависимости поверх base
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-cache-dir -r requirements/dev.txt

# =====================================================================
# Стадия 3: dev – Образ для разработки
# =====================================================================
FROM python:3.12-slim-bookworm AS dev

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Обновляем систему и устанавливаем curl для HEALTHCHECK
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем пользователя
ARG UID=1000
ARG GID=1000
RUN groupadd -r -g "${GID}" appuser && useradd -r -u "${UID}" -g appuser -d /home/appuser -m -s /bin/bash appuser

WORKDIR /app

# Копируем зависимости из dev-dependencies
COPY --from=dev-dependencies /root/.local /home/appuser/.local

# Копируем код приложения
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=10 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# =====================================================================
# Стадия 4: prod – Финальный образ для продакшена
# =====================================================================
FROM python:3.12-slim-bookworm AS prod

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Обновляем систему и устанавливаем curl для HEALTHCHECK
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем пользователя
ARG UID=1000
ARG GID=1000
RUN groupadd -r -g "${GID}" appuser && useradd -r -u "${UID}" -g appuser -d /home/appuser -m -s /bin/bash appuser

WORKDIR /app

# Копируем зависимости ТОЛЬКО из builder-base (чистые production-зависимости)
COPY --from=builder-base /root/.local /home/appuser/.local

# Копируем код приложения
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser openapi-assets.yaml .
COPY --chown=appuser:appuser static ./static
COPY --chown=appuser:appuser templates ./templates
COPY --chown=appuser:appuser init_data.py .
COPY --chown=appuser:appuser seed_devices.py .
COPY --chown=appuser:appuser create_admin.py .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
