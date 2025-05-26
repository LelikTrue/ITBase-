# Dockerfile

# Базовый образ: Python 3.11 на основе Debian Buster (легковесный).
FROM python:3.11-slim-buster

# Устанавливаем рабочую директорию внутри контейнера.
# Все последующие команды будут выполняться относительно этой директории.
WORKDIR /app

# Копируем файл зависимостей Python в рабочую директорию.
# Это делается первым, чтобы Docker мог кэшировать этот слой,
# если requirements.txt не меняется, ускоряя последующие сборки.
COPY requirements.txt .

# Установка системных зависимостей, необходимых для psycopg2-binary (драйвера PostgreSQL).
# 'build-essential' предоставляет инструменты для компиляции, 'libpq-dev' - заголовочные файлы для PostgreSQL.
# 'gcc' также часто требуется для сборки C-расширений.
# '--no-install-recommends' уменьшает количество устанавливаемых необязательных пакетов.
# 'rm -rf /var/lib/apt/lists/*' очищает кэш пакетов после установки для уменьшения размера образа.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python-зависимости из requirements.txt.
# '--no-cache-dir' отключает кэш pip для уменьшения размера образа.
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта в рабочую директорию контейнера.
# .env, alembic.ini и папка alembic должны быть в корневом каталоге вашего проекта на хосте.
# Docker копирует их в /app внутри контейнера.
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Добавляем /app в PYTHONPATH.
# Это позволяет Python находить модули внутри вашей директории 'app' (например, 'from app.db.database').
ENV PYTHONPATH=/app:$PYTHONPATH

# Открываем порт 8000. Это просто декларация, фактический проброс порта делается в docker-compose.yml.
EXPOSE 8000

# Команда, которая будет выполняться при запуске контейнера по умолчанию.
# Uvicorn запускает ваше FastAPI приложение 'app.main:app'.
# '--host 0.0.0.0' делает приложение доступным на всех сетевых интерфейсах контейнера.
# '--port 8000' указывает порт, который Uvicorn будет слушать.
# '--reload' перезагружает сервер при изменении кода (удобно для разработки).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
