# ===================================================================
# ITBase: Главный Makefile для управления Docker-окружением
# ===================================================================
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: help up down down-clean logs migrate migration init-data seed-devices dev-full wait-ready shell lint lint-fix format type-check test ps restart db-shell redis-cli clean dev prod

# --- Переменные ---
# По умолчанию используем dev-окружение
COMPOSE_FILE ?= -f docker-compose.yml -f docker-compose.dev.yml
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

## up: Собрать образы и запустить сервисы в фоновом режиме (dev)
up: check-env
	@echo "${YELLOW}Запуск окружения разработки...${RESET}"
	docker compose $(COMPOSE_FILE) up --build -d

## dev: Запуск в режиме разработки (с hot reload и логами)
dev: check-env
	@echo "${YELLOW}Запуск в режиме разработки (с логами)...${RESET}"
	docker compose $(COMPOSE_FILE) up --build

## prod: Запуск в продакшн режиме
prod: COMPOSE_FILE := -f docker-compose.yml -f docker-compose.prod.yml
prod: check-env
	@echo "${YELLOW}Запуск в продакшн режиме...${RESET}"
	docker compose $(COMPOSE_FILE) up --build -d

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

## logs: Показать логи приложения (Ctrl+C для выхода)
logs:
	@echo "${YELLOW}Просмотр логов приложения...${RESET}"
	docker compose $(COMPOSE_FILE) logs -f $(APP_SERVICE_NAME)

## restart: Перезапустить приложение
restart:
	@echo "${YELLOW}Перезапуск приложения...${RESET}"
	docker compose $(COMPOSE_FILE) restart $(APP_SERVICE_NAME)

# --- Ожидание готовности ---

## wait-ready: Ожидание готовности PostgreSQL и приложения
wait-ready:
	@echo "${YELLOW}Ожидание готовности сервисов...${RESET}"
	@timeout=60 counter=0; \
	until docker compose $(COMPOSE_FILE) ps | grep -E 'backend.*\(healthy\)' > /dev/null 2>&1; do \
		[ $$counter -ge $$timeout ] && echo "\n${RED}Ошибка: Приложение не достигло статуса 'healthy'${RESET}" && exit 1; \
		printf "."; sleep 3; counter=$$((counter+3)); \
	done
	@echo "\n${GREEN}Приложение готово!${RESET}"

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

## dev-full: Полный запуск: миграции + справочники + демо-активы
dev-full: up migrate init-data seed-devices
	@echo "\n${GREEN}Готово! Открывай: http://localhost:$(APP_PORT)/dashboard${RESET}"

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