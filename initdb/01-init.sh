#!/bin/bash
set -e

# Ждем пока PostgreSQL будет готов принимать подключения НА localhost
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "localhost" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do # <-- ИЗМЕНЕНО
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

# Проверяем, существует ли база данных НА localhost
if ! PGPASSWORD=$POSTGRES_PASSWORD psql -h "localhost" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$POSTGRES_DB"; then # <-- ИЗМЕНЕНО
  # Создаем базу данных, если она не существует
  PGPASSWORD=$POSTGRES_PASSWORD createdb -h "localhost" -U "$POSTGRES_USER" "$POSTGRES_DB" # <-- ИЗМЕНЕНО
  echo "Database $POSTGRES_DB created"
  
  # Применяем миграции
  cd /app
  alembic upgrade head
  echo "Migrations applied"
  
  # Здесь можно добавить начальные данные
  # PGPASSWORD=$POSTGRES_PASSWORD psql -h "localhost" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init-data.sql # <-- ИЗМЕНЕНО
else
  echo "Database $POSTGRES_DB already exists, skipping creation"
fi
