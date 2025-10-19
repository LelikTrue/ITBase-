.PHONY: help install dev prod test lint format migrate

# Colors
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

## Show help
display_help:
	@echo ""
	@echo "${YELLOW}ITBase Management Commands${RESET}"
	@echo ""
	@echo "Usage:"
	@echo "  make ${GREEN}<target>${RESET} ${YELLOW}[options]${RESET}"
	@echo ""
	@echo "Targets:"
	@awk '\
	/^[a-zA-Z\-]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")-1); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  ${GREEN}%-20s${RESET} %s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST) | sort
	@echo ""

## Install project dependencies
install:
	@echo "${YELLOW}Installing dependencies...${RESET}"
	pip install --upgrade pip
	pip install -r requirements/dev.txt
	pre-commit install

## Start development environment
dev: check-env
	@echo "${YELLOW}Starting development environment...${RESET}"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

## Start production environment
prod: check-env
	@echo "${YELLOW}Starting production environment...${RESET}"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

## Run tests
test: check-env
	@echo "${YELLOW}Running tests...${RESET}"
	docker-compose -f docker-compose.test.yml run --rm test

## Run linter
lint:
	@echo "${YELLOW}Running linters...${RESET}"
	flake8 app tests
	black --check app tests
	isort --check-only app tests
	mypy app

## Format code
format:
	@echo "${YELLOW}Formatting code...${RESET}"
	black app tests
	isort app tests

## Run database migrations
migrate: check-env
	@echo "${YELLOW}Running migrations...${RESET}"
	docker-compose run --rm app alembic upgrade head

## Check environment variables
check-env:
	@if [ ! -f .env ]; then \
		echo "${YELLOW}Warning: .env file not found. Creating from example...${RESET}"; \
		cp .env.example .env; \
	fi

## Show help by default
help: display_help

## Default target
default: help