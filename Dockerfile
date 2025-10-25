# =====================================================================
# Стадия 1: builder – Установка зависимостей
# =====================================================================
# Используем конкретную версию slim-образа для предсказуемости
FROM python:3.12.3-slim-bookworm AS builder

# Устанавливаем системные переменные, чтобы Python работал корректно
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Путь к пакетам, установленным через pip
    PATH="/root/.local/bin:$PATH"

# Обновляем списки пакетов и устанавливаем curl для HEALTHCHECK.
# --no-install-recommends экономит место.
# В конце чистим кэш apt, чтобы образ оставался маленьким.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем только файлы зависимостей. Это ключевой шаг для кеширования.
# Если эти файлы не меняются, Docker не будет переустанавливать зависимости.
COPY requirements/base.txt requirements/dev.txt requirements/prod.txt ./requirements/

# Устанавливаем базовые и dev-зависимости с использованием кеша pip
# Это ускорит последующие сборки
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/base.txt && \
    pip install --no-cache-dir -r requirements/dev.txt


# =====================================================================
# Стадия 2: dev – Образ для разработки
# =====================================================================
FROM builder AS dev

WORKDIR /app

# Копируем остальные файлы проекта.
# Мы делаем это после установки зависимостей, чтобы изменения в коде
# не приводили к переустановке всех пакетов.
COPY . .

# Создаем непривилегированного пользователя для безопасности
ARG UID=1000
ARG GID=1000
RUN groupadd -r -g "${GID}" appuser && useradd -r -u "${UID}" -g appuser appuser

# Меняем владельца директории приложения
RUN chown -R appuser:appuser /app

# Переключаемся на созданного пользователя
USER appuser

# Открываем порт, на котором будет работать uvicorn
EXPOSE 8000

# Healthcheck для проверки, что приложение запустилось и отвечает
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=10 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда для запуска сервера в режиме разработки с автоперезагрузкой
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# =====================================================================
# Стадия 3: prod – Финальный образ для продакшена
# =====================================================================
# Начинаем с чистого образа, чтобы он был минималистичным
FROM python:3.12.3-slim-bookworm AS prod

# Устанавливаем системные переменные для продакшена
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    # Настройки для pip
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем curl для HEALTHCHECK в production-образе
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем пользователя ПЕРЕД копированием файлов, чтобы сразу задать нужного владельца
ARG UID=1000
ARG GID=1000
RUN groupadd -r -g "${GID}" appuser && useradd -r -u "${UID}" -g appuser -d /home/appuser -m -s /bin/bash

WORKDIR /app

# Копируем установленные зависимости из стадии builder
COPY --from=builder /root/.local /home/appuser/.local
# Копируем только production-зависимости, если они есть
# RUN --mount=type=cache,target=/root/.cache/pip \
#     pip install --no-cache-dir -r requirements/prod.txt

# Копируем только нужные для работы приложения файлы с правильными правами
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser openapi-assets.yaml .
COPY --chown=appuser:appuser static ./static

# Переключаемся на нашего пользователя
USER appuser

EXPOSE 8000

# Healthcheck для продакшена с более консервативными настройками
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Команда для запуска сервера в продакшене
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
