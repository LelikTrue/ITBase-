# Project Status

🚧 **This project is currently in the early stages of development.**  
Contributions and feedback are welcome!

# Учет IT имущества 

Краткое описание проекта.

## Технологический стек

* FastAPI
* PostgreSQL
* Docker

## Начало работы

### Предварительные требования

- Docker 20.10+
- Docker Compose 2.0+
- Git (для клонирования репозитория)

### Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/it-asset-tracker.git
   cd it-asset-tracker
   ```

2. Настройте переменные окружения:
   ```bash
   cp .env.example .env
   ```
   
   Отредактируйте `.env` файл, указав необходимые настройки:
   ```env
   # Настройки базы данных
   DB_NAME=it_asset_db
   DB_USER=it_user_db
   DB_PASSWORD=secure_password
   DB_HOST=db
   
   # Настройки приложения
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   ```

3. Запустите приложение с помощью Docker Compose:
   ```bash
   docker compose up --build -d
   ```

4. После успешного запуска приложение будет доступно по адресу:
   - Веб-интерфейс: http://localhost:8000
   - API документация (Swagger UI): http://localhost:8000/docs
   - Альтернативная документация (ReDoc): http://localhost:8000/redoc
   - Adminer (управление БД): http://localhost:8080

## 📂 Структура проекта

```
├── app/                    # Исходный код приложения
│   ├── __init__.py
│   └── main.py             # Точка входа в приложение
├── static/                 # Статические файлы (CSS, JS, изображения)
│   ├── css/
│   └── js/
├── templates/              # Шаблоны Jinja2
│   ├── base.html           # Базовый шаблон
│   └── dashboard.html      # Панель управления
├── .env.example           # Пример файла переменных окружения
├── .gitignore
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile             # Конфигурация Docker
├── requirements.txt        # Зависимости Python
└── schema.sql             # SQL-схема базы данных
```



## 🔄 Работа с миграциями базы данных

Проект использует Alembic для управления миграциями базы данных. Вот основные команды:

1. Применить все ожидающие миграции:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. Создать новую миграцию (после изменения моделей):
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "Описание изменений"
   ```

3. Откатить последнюю миграцию:
   ```bash
   docker compose exec backend alembic downgrade -1
   ```

## 🛠 Доступные API эндпоинты

- `GET /` - Основная страница приложения
- `GET /dashboard` - Панель управления активами
- `GET /api/v1/assets` - Получить список активов (JSON)
- `GET /docs` - Интерактивная документация API (Swagger)
- `GET /redoc` - Альтернативная документация (ReDoc)

## 🔒 Аутентификация

Для доступа к защищенным эндпоинтам требуется аутентификация. Используйте:

```bash
curl -X 'GET' \
  'http://localhost:8000/api/protected-route' \
  -H 'Authorization: Bearer your-jwt-token'
```

## 🛑 Остановка приложения

Для остановки всех контейнеров выполните:

```bash
docker compose down
```

Для полной очистки (включая тома с данными):

```bash
docker compose down -v
```

## 🧪 Тестирование

Для запуска тестов выполните:

```bash
docker compose exec backend pytest
```

## Дополнительная информация

Здесь можно добавить любую другую релевантну информацию о проекте.
