# IT Asset Tracker

Система учета IT-активов предприятия, разработанная на базе FastAPI и PostgreSQL. Позволяет эффективно управлять оборудованием, отслеживать его состояние и местоположение.

## 🚀 Возможности

- 📋 Учет IT-оборудования с детализацией по типам и характеристикам
- 📊 Просмотр и управление активами через веб-интерфейс
- 🔍 Поиск и фильтрация активов по различным параметрам
- 📱 Адаптивный интерфейс с поддержкой мобильных устройств
- 🔒 Безопасное хранение данных с разграничением прав доступа
- 📈 Готовое API для интеграции с другими системами

## 🛠 Технологический стек

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0
- **Frontend**: HTML5, Jinja2, Bootstrap 5, JavaScript
- **База данных**: PostgreSQL 13
- **Развертывание**: Docker, Docker Compose
- **Инструменты**: Alembic (миграции), Pydantic (валидация данных)

## 🚀 Быстрый старт

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

## 🔄 Разработка

1. Установите зависимости разработки:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Запустите линтеры:
   ```bash
   flake8 app
   black --check app
   ```

3. Проверьте типы:
   ```bash
   mypy app
   ```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой фичи (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add some amazing feature'`)
4. Отправьте изменения в форк (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для получения дополнительной информации.

## ✉️ Контакты

По вопросам и предложениям обращайтесь:
- Email: your.email@example.com
- Проект: [https://github.com/yourusername/it-asset-tracker](https://github.com/yourusername/it-asset-tracker)
