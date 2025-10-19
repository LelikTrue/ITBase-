# ===================================================================
# ITBase: Главный Makefile для управления Docker-окружением
# ===================================================================

.PHONY: help up down logs migrate migration shell lint format test

# --- Переменные ---
# Используем docker-compose.dev.yml как основной файл для разработки
COMPOSE_FILE := -f docker-compose.dev.yml
# Имя сервиса приложения из docker-compose файла
APP_SERVICE_NAME := app

# --- Цвета для вывода ---
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
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
			printf "  ${GREEN}%-12s${RESET} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST) | sort
	@echo ""

# --- Управление окружением ---

## up: Собрать образы и запустить все сервисы в фоновом режиме
up: check-env
	@echo "${YELLOW}🚀 Запуск окружения разработки...${RESET}"
	docker compose $(COMPOSE_FILE) up --build -d

## down: Остановить и удалить все сервисы
down:
	@echo "${YELLOW}🛑 Остановка окружения разработки...${RESET}"
	docker compose $(COMPOSE_FILE) down

## logs: Показать логи запущенного приложения (нажмите Ctrl+C для выхода)
logs:
	@echo "${YELLOW}📋 Просмотр логов приложения...${RESET}"
	docker compose $(COMPOSE_FILE) logs -f $(APP_SERVICE_NAME)

# --- Работа с базой данных ---

## migrate: Применить миграции Alembic к базе данных
migrate:
	@echo "${YELLOW}🔄 Применение миграций к БД...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) alembic upgrade head

## migration: Создать новый файл миграции Alembic
migration:
	@read -p "${YELLOW}Введите описание для новой миграции (например, 'add_user_model'): ${RESET}" MSG; \
	echo "${YELLOW}📝 Создание файла миграции...${RESET}"; \
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) alembic revision --autogenerate -m "$$MSG"

## seed-devices: Наполнить БД демо-активами (устройствами)
seed-devices:
	@echo "${YELLOW}🌱 Наполнение базы данных демо-активами...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) python seed_devices.py

# --- Инструменты разработки ---

## shell: Открыть интерактивную сессию (bash) внутри контейнера приложения
shell:
	@echo "${YELLOW}💻 Подключение к контейнеру приложения...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) bash

## lint: Проверить стиль кода с помощью линтеров внутри контейнера
lint:
	@echo "${YELLOW}🔍 Проверка стиля кода (linting)...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) flake8 .
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) black --check .
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) isort --check-only .

## format: Отформатировать код автоматически внутри контейнера
format:
	@echo "${YELLOW}✨ Автоматическое форматирование кода...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) black .
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) isort .

## test: Запустить тесты (pytest) внутри контейнера
test:
	@echo "${YELLOW}🧪 Запуск тестов...${RESET}"
	docker compose $(COMPOSE_FILE) exec $(APP_SERVICE_NAME) pytest

# --- Вспомогательные команды ---

# Проверяет наличие .env файла и создает его из .env.example, если он отсутствует
check-env:
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Внимание: .env файл не найден. Создаю из .env.example...${RESET}"; \
		cp .env.example . .env; \
	fi

# Команда по умолчанию
default: help