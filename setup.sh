#!/bin/bash
set -e

# Установка прав на скрипты
chmod +x ./*.sh 2>/dev/null || true
chmod +x ./scripts/*.sh 2>/dev/null || true

# Создаем .env, если его нет
if [ ! -f .env ]; then
    echo "Создаем .env файл из .env.example"
    cp .env.example .env
    echo "Пожалуйста, отредактируйте .env файл и настройте переменные окружения"
    exit 1
fi

# Устанавливаем права на .env
chmod 600 .env

echo "Настройка окружения завершена успешно!"
echo "Для запуска в режиме разработки выполните: docker compose up --build"
echo "Для запуска в продакшне выполните: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
