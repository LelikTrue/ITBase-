# Руководство по установке и запуску

## Требования

- Docker 20.10+ и Docker Compose 1.29+
- Git
- Bash (для выполнения скриптов)

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/LelikTrue/ITBase-.git
   cd ITBase-
   ```
   
   Или, если используете SSH:
   ```bash
   git clone git@github.com:LelikTrue/ITBase-.git
   cd ITBase-
   ```

2. Настройте окружение:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   Отредактируйте файл `.env` при необходимости.

## Запуск в режиме разработки

```bash
docker-compose up --build
```

Приложение будет доступно по адресу: http://localhost:8000

## Запуск в продакшн режиме

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Доступные сервисы

- FastAPI приложение: http://localhost:8000
- Документация API: http://localhost:8000/docs
- Adminer (управление БД): http://localhost:8080

## Распространенные проблемы

1. **Проблемы с правами доступа**
   - Убедитесь, что у вас есть права на запись в директорию проекта
   - Запустите `chmod +x setup.sh`

2. **Проблемы с портами**
   - Если порты 8000, 8080 или 5432 заняты, измените их в `.env` файле

3. **Проблемы с БД**
   - Если база данных не запускается, попробуйте:
     ```bash
     docker-compose down -v
     docker-compose up -d db
     ```

## Разработка

- Для применения миграций:
  ```bash
  docker-compose exec backend alembic upgrade head
  ```

- Для создания новой миграции:
  ```bash
  docker-compose exec backend alembic revision --autogenerate -m "description"
  ```

## Логи

Просмотр логов бэкенда:
```bash
docker-compose logs -f backend
```

Просмотр логов базы данных:
```bash
docker-compose logs -f db
```
