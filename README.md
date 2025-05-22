# Учет IT имущества

Краткое описание проекта.

## Технологический стек

* FastAPI
* PostgreSQL
* Docker

## Начало работы

### Предварительные требования

* Docker
* Docker Compose

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone <URL репозитория>
   cd <название папки проекта>
   ```
2. Создайте файл `.env` из `.env.example` и заполните необходимые переменные окружения:
   ```bash
   cp .env.example .env
   ```
   Отредактируйте `.env`:
   ```env
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=your_db_name
   # ... другие переменные ...
   ```
3. Соберите и запустите контейнеры:
   ```bash
   docker-compose up --build -d
   ```

Приложение будет доступно по адресу `http://localhost:8000`.

## Структура проекта

```
├── app/                  # Код приложения FastAPI
│   ├── __init__.py
│   └── main.py           # Основной файл FastAPI
├── docker-compose.yml    # Конфигурация Docker Compose
├── .env.example          # Пример файла переменных окружения
├── .gitignore            # Файлы, игнорируемые Git
├── requirements.txt      # Зависимости Python
├── schema.sql            # SQL-схема базы данных
└── README.md             # Этот файл
```

## Применение миграций базы данных (если используется Alembic или подобное)

Если вы используете Alembic для миграций:

1. Войдите в контейнер приложения:
   ```bash
   docker-compose exec app bash
   ```
2. Примените миграции:
   ```bash
   alembic upgrade head
   ```

## Остановка приложения

```bash
docker-compose down
```

## Дополнительная информация

Здесь можно добавить любую другую релевантну информацию о проекте.
