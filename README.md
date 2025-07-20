# Система управления ИТ-активами (ITBase)

[![GitHub license](https://img.shields.io/github/license/LelikTrue/ITBase-?style=flat-square)](https://github.com/LelikTrue/ITBase-/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square)](https://github.com/pre-commit/pre-commit)

## 🚧 **СТАТУС ПРОЕКТА: АКТИВНАЯ РАЗРАБОТКА**

> **Проект находится на стадии активной разработки. Добро пожаловать к сотрудничеству и обратной связи!** 🤝

### 🛠️ Development Setup

1. **Установка зависимостей:**
   ```bash
   # Установка зависимостей
   pip install -r requirements/dev.txt
   
   # Установка pre-commit хуков
   pre-commit install
   ```

2. **Запуск линтеров и форматтеров:**
   ```bash
   # Автоформатирование кода
   black .
   isort .
   
   # Проверка стиля кода
   flake8
   mypy .
   ```

3. **Запуск тестов:**
   ```bash
   # Запуск всех тестов
   pytest
   
   # С покрытием кода
   pytest --cov=app --cov-report=term-missing
   ```

4. **Запуск в режиме разработки:**
   ```bash
   # С использованием Docker
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
   
   # Или напрямую
   uvicorn app.main:app --reload
   ```

### ✅ **Последние обновления:**

- Добавлена интеграция pre-commit с линтерами и форматтерами
- Настроены GitHub Actions для CI/CD
- Добавлены health checks для мониторинга работоспособности сервиса
- Реализованы эндпоинты для Kubernetes liveness/readiness пробы
- Улучшена обработка ошибок и логирование
- Обновлены конфигурации Docker для продакшена
- Добавлены ограничения ресурсов и политики перезапуска
- Улучшена безопасность с помощью non-root пользователей в контейнерах

🔗 **Репозиторий:** [https://github.com/LelikTrue/ITBase-](https://github.com/LelikTrue/ITBase-)

## 🚀 Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/LelikTrue/ITBase-.git
   cd ITBase-
   ```

2. **Настройка окружения:**
   ```bash
   # Создайте файл .env из примера
   cp .env.example .env
   
   # Установите зависимости
   pip install -r requirements/dev.txt
   pre-commit install
   ```

   > ⚠️ **Важно для продакшена**: При развертывании на сервере обязательно установите `DEBUG=False` в файле `.env` и используйте надежные, сгенерированные пароли и `SECRET_KEY`!

## 🚀 Запуск приложения

### Локальная разработка с hot-reload
Для локальной разработки с автоматической перезагрузкой при изменениях:
```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up --build
```

### Полный dev-стек
Для запуска всего стека разработки (бэкенд, БД, Adminer):
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Продакшн-режим
Для запуска в продакшн-режиме:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 🚀 Первый запуск на сервере (пошаговая инструкция)

Для абсолютных новичков - последовательность действий при первом развертывании на сервере:

1. **Клонирование и переход в директорию:**
   ```bash
   git clone https://github.com/LelikTrue/ITBase-.git
   cd ITBase-
   ```

2. **Настройка конфигурации для продакшена:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл:
   # - Установите DEBUG=False
   # - Смените пароли на надежные
   # - Сгенерируйте новый SECRET_KEY
   ```

3. **Запуск продакшн-контейнеров:**
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

4. **Создание таблиц в базе данных (критически важно!):**
   ```bash
   docker compose exec backend alembic upgrade head
   ```

   > ⚠️ **Важно**: Этот шаг обязателен после первого запуска для создания всех необходимых таблиц в базе данных.

### Тестирование

Для запуска тестов:
```bash
docker compose -f docker-compose.test.yml run --rm test
```

### CI/CD сценарии

Для использования в CI/CD пайплайнах:
```bash
docker compose -f docker-compose.ci.yml up --exit-code-from app
```

## 🔌 Доступ к сервисам

**Для локальной разработки:**

- **Основное приложение**: <http://localhost:8000>
- **Документация API (Swagger UI)**: <http://localhost:8000/docs>
- **Документация API (ReDoc)**: <http://localhost:8000/redoc>
- **Adminer (управление БД)**: <http://localhost:8080>
  - Система: PostgreSQL
  - Сервер: db
  - Пользователь: ${POSTGRES_USER:-postgres}
  - Пароль: ${POSTGRES_PASSWORD:-postgres}
  - База данных: ${POSTGRES_DB:-itbase}

**Для продакшн-сервера:**
> При развертывании на сервере используйте `http://<IP-адрес_вашего_сервера>:8000` вместо `localhost`

## 🛠 Полезные команды

### Управление контейнерами
```bash
# Остановить все контейнеры
docker compose down

# Остановить и удалить тома
docker compose down -v

# Пересобрать конкретный сервис (например, backend)
docker compose build backend

# Обновить образы и перезапустить
docker compose pull && docker compose up -d

# Просмотр логов сервиса
docker compose logs -f backend
```

### Управление базой данных
```bash
# Применить миграции
docker compose exec backend alembic upgrade head

# Создать новую миграцию
docker compose exec backend alembic revision --autogenerate -m "описание изменений"

# Откатить последнюю миграцию
docker compose exec backend alembic downgrade -1
```

Подробные инструкции смотрите в [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 О проекте

**Система управления ИТ-активами (ITBase)** - это надежное решение для отслеживания и управления ИТ-активами организации. Она предоставляет централизованную платформу для мониторинга оборудования, программного обеспечения, лицензий и других важных ИТ-ресурсов, обеспечивая актуальную информацию и эффективное управление ИТ-инфраструктурой.

## 🚀 Основные функции

- **Централизованное отслеживание активов**: Полный обзор всех ИТ-активов.
- **Подробная информация об активах**: Хранение и получение детальной информации об активе (тип, статус, модель, отдел, местоположение, сотрудник).
- **Обзор панели управления**: Интуитивно понятная панель управления для анализа активов.
- **API-интерфейсы**: Высокопроизводительные API для взаимодействия с данными.
- **Удобный веб-интерфейс**: Интуитивно понятный веб-интерфейс с вкладочной структурой форм.
- **Контейнеризация**: Легкое и консистентное развертывание.
- **Валидация данных**: Безопасная обработка форм с защитой от некорректных значений.
- **Тестовые данные**: Автозаполнение форм для быстрого тестирования функциональности.
- **Журнал аудита**: Отслеживание всех изменений в системе.

## 🌐 Доступные эндпоинты

### Веб-интерфейс

- `GET /` - Перенаправляет на панель управления
- `GET /dashboard` - Основная панель управления активами
- `GET /add` - Форма добавления нового актива
- `GET /edit/{device_id}` - Форма редактирования существующего актива

### API

- `GET /dashboard` - Получение данных для дашборда с пагинацией (HTML)
- `POST /create` - Создание нового актива
- `GET /edit/{device_id}` - Форма редактирования актива (HTML)
- `POST /update/{device_id}` - Обновление существующего актива
- `POST /delete/{device_id}` - Удаление актива

### Мониторинг и здоровье системы

- `GET /health` - Проверка работоспособности сервиса (liveness probe)
- `GET /ready` - Проверка готовности сервиса (readiness probe)
- `GET /api/health` - Расширенная проверка состояния API и зависимостей
- `GET /api/health/ready` - Проверка готовности всех компонентов
- `GET /api/health/startup` - Проверка успешного запуска

### Дополнительные функции

- `GET /audit-logs` - Просмотр журнала аудита
- Улучшенная обработка фильтров журнала аудита для предотвращения ошибок 422 (Unprocessable Entity)
- Автозаполнение форм тестовыми данными
- Валидация данных с безопасной обработкой пустых значений
- Глобальная обработка ошибок и логирование

### Документация

- `GET /docs` - Интерактивная документация API (Swagger UI)
- `GET /redoc` - Альтернативная документация API (ReDoc)

## ⚙️ Технологический стек

Проект построен на основе надежного и современного технологического стека:

### Бэкенд

- **FastAPI 0.115.12** - Высокопроизводительный веб-фреймворк для создания API на Python
- **SQLAlchemy 2.0** - ORM для работы с базой данных
- **Alembic 1.13.1** - Управление миграциями базы данных
- **Pydantic 2.7.1** - Валидация данных и настройки приложения

### База данных

- **PostgreSQL** - Надежная реляционная СУБД
- **psycopg2** - Адаптер PostgreSQL для Python

### Фронтенд

- **Jinja2 3.1.4** - Шаблонизатор для генерации HTML
- **Bootstrap 5** - CSS-фреймворк для адаптивного дизайна
- **jQuery** - Библиотека для работы с DOM и AJAX

### Аутентификация и безопасность

- **JWT (JSON Web Tokens)** - Для аутентификации API
- **Passlib** - Для безопасного хеширования паролей
- **itsdangerous** - Для подписи и шифрования данных

### Утилиты

- **python-dotenv** - Управление переменными окружения
- **python-dateutil** - Расширенные функции работы с датами
- **pytz** - Поддержка часовых поясов

### Разработка и тестирование

- **Uvicorn** - ASGI-сервер для запуска приложения
- **pytest** - Фреймворк для тестирования
- **black, isort** - Форматирование кода

### Развертывание

- **Docker** - Контейнеризация приложения
- **Docker Compose** - Оркестрация контейнеров
- **Nginx** - Обратный прокси и балансировщик нагрузки

## 🏁 Начало работы

### Предварительные требования

Прежде чем начать, убедитесь, что у вас установлены следующие компоненты:

- Docker (рекомендуется версия 20.10+)
- Docker Compose (рекомендуется версия 2.0+)
- Git (для клонирования репозитория)

### Установка и запуск

1. **Клонирование репозитория:**

    ```bash
    git clone https://github.com/LelikTrue/ITBase-.git
    cd ITBase
    ```

2. **Настройка переменных окружения:**

    Создайте файл `.env`, скопировав пример и отредактируйте его с учетом ваших настроек:

    ```bash
    cp .env.example .env
    ```

    Откройте файл `.env` и настройте необходимые параметры:

    ```ini
    # Настройки базы данных
    DB_NAME=it_asset_db
    DB_USER=it_user_db
    DB_PASSWORD=secure_password
    DB_HOST=db

    # Настройки приложения
    DEBUG=True
    SECRET_KEY=your-strong-random-secret-key-here
    ```

3. **Запуск приложения с помощью Docker Compose:**

    Эта команда создает необходимые Docker-образы, создает контейнеры и запускает все сервисы в фоновом режиме (`-d`).

    ```bash
    docker compose build
    docker compose up -d
    ```

    **Примечание:** FastAPI приложение запускается внутри контейнера на порту `8000`. Доступ осуществляется напрямую через порт `8000`. Adminer доступен на стандартном порту `8080`.

   ## 📂 Структура проекта

Проект следует модульной структуре для удобства навигации и дальнейшей разработки. Основные компоненты и их назначение приведены ниже:

**********************************

```plaintext
ITBase/
├── app/
│   ├── api/
│   │   └── endpoints/
│   │       ├── assets.py              # Основные CRUD операции для активов
│   │       ├── audit_logs.py          # API для журнала аудита
│   │       ├── audit_log_ui.py        # UI для журнала аудита
│   │       └── delete_device.py       # Функционал удаления устройств
│   ├── db/
│   │   └── database.py               # Настройки подключения к БД
│   ├── models/
│   │   ├── action_log.py             # Модель журнала действий
│   │   ├── asset.py                  # Основные модели (Device, AssetType и др.)
│   │   ├── asset_type.py
│   │   ├── attachment.py
│   │   ├── base.py
│   │   ├── department.py
│   │   ├── device.py
│   │   ├── device_model.py
│   │   ├── device_status.py
│   │   ├── employee.py
│   │   ├── location.py
│   │   ├── manufacturer.py
│   │   └── __init__.py
│   ├── schemas/                      # Pydantic схемы для валидации
│   │   ├── asset.py
│   │   ├── audit_log.py
│   │   └── device.py
│   ├── services/                     # Бизнес-логика приложения
│   │   ├── asset_type.py
│   │   ├── audit_log_service.py
│   │   ├── base.py
│   │   ├── device.py
│   │   └── __init__.py
│   ├── templates/                    # Дублирующиеся шаблоны (устаревшие)
│   │   ├── audit_logs.html
│   │   └── base.html
│   ├── config.py                     # Конфигурация приложения
│   ├── main.py                       # Точка входа FastAPI приложения
│   └── __init__.py
├── static/
│   ├── test_data/
│   │   └── device_fixture.json       # Тестовые данные для форм
│   ├── dark_theme.css               # Темная тема CSS
│   └── main.css                     # Основные стили
├── templates/                        # Основные HTML шаблоны
│   ├── add_asset.html               # Форма добавления актива
│   ├── base.html                    # Базовый шаблон
│   ├── dashboard.html               # Главная панель управления
│   ├── edit_asset.html              # Форма редактирования актива
│   └── error.html                   # Страница ошибок
├── alembic/                         # Миграции базы данных
│   ├── versions/                    # Файлы миграций
│   └── env.py
├── .env.example                     # Пример переменных окружения
├── .gitignore
├── alembic.ini                     # Конфигурация Alembic
├── docker-compose.yml              # Основная Docker конфигурация
├── docker-compose.override.yml     # Переопределения для разработки
├── docker-compose.prod.yml         # Продакшн конфигурация
├── Dockerfile                      # Образ для разработки
├── Dockerfile.prod                 # Продакшн образ
├── requirements.txt                # Python зависимости
├── setup.sh                        # Скрипт настройки окружения
├── demo_data.sql                   # Демо данные для БД
├── schema.sql                      # Схема базы данных
├── CONTRIBUTING.md                 # Руководство по участию
└── README.md                       # Документация проекта
```

**********************************

## Часть 4: Миграции базы данных, API-конечные точки, Аутентификация

## 🔄 Миграции базы данных (Alembic)

Проект использует Alembic для управления схемой базы данных. Вот основные команды:

1. **Применение всех ожидающих миграций:**

    ```bash
    docker compose exec backend alembic upgrade head
    ```

2. **Создание новой миграции** (после внесения изменений в модели SQLAlchemy):

    ```bash
    docker compose exec backend alembic revision --autogenerate -m "Описание ваших изменений"
    ```

3. **Откат последней миграции:**

    ```bash
    docker compose exec backend alembic downgrade -1
    ```

## 🛠 Доступные API-конечные точки

- **GET /** - Перенаправляет на панель управления.
- **GET /dashboard** - Основной веб-интерфейс для обзора ИТ-активов.
- **GET /api/v1/assets** - Получение списка всех активов (конечная точка JSON API).
- **POST /api/v1/assets** - Добавление нового актива.
- **GET /assets/add** - Веб-форма для добавления нового актива.
- **GET /docs** - Интерактивная документация API (Swagger UI).
- **GET /redoc** - Альтернативная документация API (ReDoc).

## 🔒 Аутентификация (если применимо)

*Этот раздел будет заполнен после реализации аутентификации. Пока это заглушка.*

В настоящее время проект сосредоточен на основной функциональности управления активами. Механизмы аутентификации будут интегрированы в будущих фазах разработки.

**Часть 5: Остановка приложения, Тестирование, Лицензия**

## 🛑 Остановка приложения

Для остановки всех запущенных контейнеров Docker проекта:

```bash
docker compose down
```

Для остановки всех контейнеров и удаления томов (например, для очистки данных базы данных):

```bash
docker compose down -v
```

## 🧪 Тестирование

Для запуска тестов проекта:

```bash
docker compose exec backend pytest
```

## 📄 Лицензия

Этот проект является открытым исходным кодом и доступен под лицензией MIT.
