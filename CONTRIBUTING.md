# Руководство для участников проекта

Благодарим за интерес к проекту ITBase! Это руководство поможет вам принять участие в разработке.

## 🚀 Начало работы

### Требования

- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Git 2.25+
- Poetry 1.6+ (для управления зависимостями)

### Установка

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/LelikTrue/ITBase-.git
   cd ITBase-
   ```

2. **Настройте виртуальное окружение и зависимости:**
   ```bash
   # Создайте и активируйте виртуальное окружение
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # Или на Windows:
   # .\venv\Scripts\activate

   # Установите зависимости
   pip install -r requirements/dev.txt
   pre-commit install
   ```

3. **Настройте переменные окружения:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env по необходимости
   ```

## 🛠️ Разработка

### Запуск в режиме разработки

```bash
# Запуск сервера разработки
uvicorn app.main:app --reload

# Или с помощью Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Форматирование кода

Проект использует автоматическое форматирование с помощью Black и isort:

```bash
# Автоматическое форматирование
black .
isort .

# Проверка стиля кода
flake8
```

### Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием кода
pytest --cov=app --cov-report=term-missing

# Запуск конкретного теста
pytest tests/path/to/test_file.py::test_function
```

### Миграции базы данных

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

## 🤝 Как внести вклад

1. **Создайте ветку** для вашего изменения:
   ```bash
   git checkout -b feature/feature-name
   # Или для исправления бага:
   # git checkout -b bugfix/description
   ```

2. **Сделайте коммиты** с понятными сообщениями:
   ```bash
   git add .
   git commit -m "feat: добавить новую функциональность"
   # Или:
   # fix: исправить баг в модуле X
   # docs: обновить документацию
   # style: отформатировать код
   # test: добавить тесты
   # refactor: рефакторинг кода
   # chore: обновить зависимости
   ```

3. **Запустите тесты** и проверки кода:
   ```bash
   pre-commit run --all-files
   pytest
   ```

4. **Отправьте изменения** в ваш форк:
   ```bash
   git push origin feature/feature-name
   ```

5. **Создайте Pull Request** в основную ветку проекта.

## 🧪 Непрерывная интеграция

Каждый PR автоматически проверяется с помощью GitHub Actions. Убедитесь, что все тесты проходят успешно перед отправкой на ревью.

## 🔒 Безопасность

Если вы нашли уязвимость, пожалуйста, не создавайте публичный issue. Вместо этого отправьте письмо на devkerch@gmail.com.

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для получения дополнительной информации.

## 🙏 Благодарности

Спасибо всем, кто вносит свой вклад в развитие проекта!
## Распространенные проблемы

1. **Проблемы с правами доступа**
   - Убедитесь, что у вас есть права на запись в директорию проекта
   - Запустите `chmod +x setup.sh`

2. **Проблемы с портами**
   - Если порты 8000, 8080 или 5432 заняты, измените их в `.env` файле

3. **Проблемы с БД**
   - Если база данных не запускается, попробуйте:
     ```bash
     docker compose down -v
     docker compose up -d db
     ```

## Разработка

- Для применения миграций:
  ```bash
  docker compose exec backend alembic upgrade head
  ```

- Для создания новой миграции:
  ```bash
  docker compose exec backend alembic revision --autogenerate -m "description"
  ```

## Логи

Просмотр логов бэкенда:
```bash
docker compose logs -f backend
```

Просмотр логов базы данных:
```bash
docker compose logs -f db
```
