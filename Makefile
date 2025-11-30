# ===================================================================
# ITBase: Главный Makefile для управления Docker-окружением
# ===================================================================
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: help up down down-clean rebuild-db logs logs-clear logs-db migrate migration init-data seed-devices dev-full wait-ready shell lint lint-fix format type-check test ps restart db-shell redis-cli clean dev prod

# --- Переменные ---
# По умолчанию используем dev-окружение
COMPOSE_FILE ?= -f docker-compose.yml -f docker-compose.dev.yml
PROD_COMPOSE_FILE := -f docker-compose.yml -f docker-compose.prod.yml
APP_SERVICE_NAME := backend
# Используем порт из .env, если он есть, иначе - 8002
APP_PORT := $(shell grep APP_PORT .env 2>/dev/null | cut -d '=' -f2 || echo 8002)

# --- Цвета для вывода ---
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RED    := $(shell tput -Txterm setaf 1)
RESET  := $(shell tput -Txterm sgr0)

## help: Показать это справочное сообщение
help:
	@echo ""
	@echo "${YELLOW}ITBase: Команды для управления окружением разработки${RESET}"
	@echo ""
	@echo "Usage: make ${GREEN}<команда>${RESET}"
	@echo ""
	@echo "Основные команды:"
	@awk '/^[a-zA-Z\.\-]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  ${GREEN}%-20s${RESET} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST) | sort
	@echo ""

# --- Управление окружением ---

## up: Собрать образы и запустить сервисы в фоновом режиме
up: check-env
	@echo "${YELLOW}Запуск сервисов...${RESET}"
	docker compose $(COMPOSE_FILE) up --build -d

## dev: Запуск в режиме разработки (с hot reload и логами)
dev: check-env
	@echo "${YELLOW}Запуск в режиме разработки (с логами)...${RESET}"
	docker compose $(COMPOSE_FILE) up --build



## ps: Показать статус всех сервисов
ps:
	@echo "${YELLOW}Статус сервисов:${RESET}"
	docker compose $(COMPOSE_FILE) ps

## down: Остановить и удалить все сервисы
down:
	@echo "${YELLOW}Остановка окружения...${RESET}"
	docker compose $(COMPOSE_FILE) down

## down-clean: Остановить, удалить контейнеры и volume (полная очистка)
down-clean:
	@echo "${YELLOW}Полная очистка (контейнеры + volume)...${RESET}"
	docker compose $(COMPOSE_FILE) down -v --remove-orphans

## rebuild-db: Пересоздать базу данных (при проблемах с версиями PostgreSQL)
rebuild-db:
	@echo "${RED}⚠️  Внимание! Это удалит ВСЕ данные из базы данных!${RESET}"
	@read -p "Продолжить? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "${YELLOW}Остановка контейнеров...${RESET}"; \
		docker compose $(COMPOSE_FILE) down; \
		echo "${YELLOW}Удаление volume базы данных...${RESET}"; \
		docker volume rm ${COMPOSE_PROJECT_NAME:-itbase}_postgres_data 2>/dev/null || true; \
		echo "${GREEN}База данных будет пересоздана при следующем запуске (make up)${RESET}"; \
	else \
		echo "${YELLOW}Отменено.${RESET}"; \
	fi

## logs: Показать логи приложения (Ctrl+C для выхода)
logs:
	@echo "${YELLOW}Логи приложения (Ctrl+C для выхода):${RESET}"
	docker compose $(COMPOSE_FILE) logs -f $(APP_SERVICE_NAME)

## logs-clear: Очистить логи (остановка и повторный запуск)
logs-clear:
	@echo "${YELLOW}Очистка логов через пересоздание контейнеров...${RESET}"
	@echo "${YELLOW}Остановка контейнеров...${RESET}"
	docker compose $(COMPOSE_FILE) down
	@echo "${YELLOW}Запуск контейнеров заново...${RESET}"
	docker compose $(COMPOSE_FILE) up -d
	@echo "${GREEN}✓ Контейнеры пересозданы, логи полностью очищены${RESET}"
	@echo "${GREEN}Приложение доступно на http://localhost:$(APP_PORT)${RESET}"

## logs-db: Показать логи базы данных (для диагностики)
logs-db:
	@echo "${YELLOW}Просмотр логов базы данных...${RESET}"
	docker compose $(COMPOSE_FILE) logs -f db

## restart: Перезапустить приложение
restart:
	@echo "${YELLOW}Перезапуск приложения...${RESET}"
	docker compose $(COMPOSE_FILE) restart $(APP_SERVICE_NAME)

# --- Ожидание готовности ---

## wait-ready: Ожидание готовности PostgreSQL и приложения
wait-ready:
	@echo "${YELLOW}Ожидание готовности сервисов...${RESET}"
	@sleep 5
	@curl -sf http://localhost:${APP_PORT:-8002}/health > /dev/null 2>&1 || (echo "${RED}Приложение не готово, но продолжаем...${RESET}")
	@echo "${GREEN}Приложение запущено!${RESET}"

# --- Работа с базой данных ---

## migrate: Применить миграции Alembic к базе данных
migrate: wait-ready
	@echo "${YELLOW}Применение миграций к БД...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) alembic upgrade head

## migration: Создать новый файл миграции Alembic
migration: wait-ready
	@read -p "${YELLOW}Введите описание для новой миграции: ${RESET}" MSG; \
	echo "${YELLOW}Создание файла миграции...${RESET}"; \
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) alembic revision --autogenerate -m "$$MSG"

## init-data: Заполнить справочники (типы, модели, статусы, отделы и т.д.)
init-data: wait-ready
	@echo "${YELLOW}Заполнение справочников...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) python -m init_data

## seed-devices: Наполнить БД демо-активами (30 устройств)
seed-devices: wait-ready
	@echo "${YELLOW}Создание 30 демо-активов...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) python -m seed_devices

## create-admin: Создать администратора системы
create-admin: wait-ready
	@echo "${YELLOW}Создание администратора...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) python create_admin.py

## full: Полный запуск: миграции + справочники + демо-активы
full: up migrate init-data seed-devices
	@echo "\n${GREEN}Готово! Открывай: http://localhost:$(APP_PORT)/dashboard${RESET}"

## dev-full: Алиас для full
dev-full: full

# --- Продакшн команды ---
# Используем паттерн prod-% для запуска любой команды в продакшн режиме
# Например: make prod-migrate, make prod-full, make prod-logs

## prod: Запуск в продакшн режиме
prod: prod-up

prod-%:
	@$(MAKE) $* COMPOSE_FILE="$(PROD_COMPOSE_FILE)"


# --- Инструменты разработки ---

## shell: Открыть bash в контейнере приложения
shell:
	@echo "${YELLOW}Подключение к контейнеру приложения...${RESET}"
	@docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) bash

## db-shell: Подключиться к базе данных PostgreSQL
db-shell:
	@echo "${YELLOW}Подключение к PostgreSQL...${RESET}"
	docker compose $(COMPOSE_FILE) exec db psql -U $$(grep POSTGRES_USER .env | cut -d '=' -f2) -d $$(grep POSTG-RES_DB .env | cut -d '=' -f2)

## redis-cli: Подключиться к Redis
redis-cli:
	@echo "${YELLOW}Подключение к Redis...${RESET}"
	docker compose $(COMPOSE_FILE) exec redis redis-cli -a $$(grep REDIS_PASSWORD .env | cut -d '=' -f2)

## lint: Проверить стиль кода с помощью Ruff
lint:
	@echo "${YELLOW}Проверка стиля кода (Ruff)...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) ruff check .

## lint-fix: Автоматически исправить ошибки стиля
lint-fix:
	@echo "${YELLOW}Автоисправление стиля кода...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) ruff check --fix .

## format: Отформатировать код (Ruff format)
format:
	@echo "${YELLOW}Форматирование кода...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) ruff format .

## type-check: Проверить типы с помощью mypy
type-check:
	@echo "${YELLOW}Проверка типов...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) mypy app/

## test: Запустить тесты (pytest)
test:
	@echo "${YELLOW}Запуск тестов...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) pytest

## clean: Очистить кеш и временные файлы
clean:
	@echo "${YELLOW}Очистка кеша и временных файлов...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) find . -type f -name "*.pyc" -delete 2>/dev/null || true

# --- Вспомогательные ---

check-env:
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Внимание: .env файл не найден. Создаю из .env.example...${RESET}"; \
		cp .env.example .env; \
		echo "${RED}⚠️  ОБЯЗАТЕЛЬНО отредактируйте файл .env и установите безопасные пароли!${RESET}"; \
		echo "${RED}   Особенно: SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD${RESET}"; \
		exit 1; \
	fi
	@if grep -q "change-me\|your-super-secret-key\|changeme" .env; then \
		echo "${RED}⚠️  ОБЯЗАТЕЛЬНО измените значения по умолчанию в .env файле!${RESET}"; \
		echo "${RED}   SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD должны быть изменены${RESET}"; \
		exit 1; \
	fi

# По умолчанию — помощь
default: help