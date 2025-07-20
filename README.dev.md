# ITBase - Быстрый старт для разработки

## 🚀 Быстрый запуск (без Docker)

### 1. Автоматическая настройка
```bash
# Клонируйте репозиторий (если еще не сделали)
git clone https://github.com/LelikTrue/ITBase-.git
cd ITBase-

# Запустите автоматическую настройку
python setup_dev.py
```

### 2. Настройка базы данных
Отредактируйте файл `.env` и укажите настройки вашей PostgreSQL:
```env
DB_HOST=10.20.30.40  # или localhost
DB_NAME=it_asset_db
DB_USER=it_user_db
DB_PASSWORD=it_pass2011
DB_PORT=5432
```

### 3. Запуск приложения
```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# Или напрямую
python run_dev.py
```

## 🛠️ Полезные команды

### Основные команды
```bash
# Запуск с установкой зависимостей
python run_dev.py --install

# Запуск с применением миграций
python run_dev.py --migrate

# Использование Makefile (если установлен make)
make -f Makefile.dev help    # Показать все команды
make -f Makefile.dev setup   # Настройка проекта
make -f Makefile.dev run     # Запуск сервера
```

### Работа с базой данных
```bash
# Применить миграции
venv\Scripts\python -m alembic upgrade head

# Создать новую миграцию
venv\Scripts\python -m alembic revision --autogenerate -m "описание"

# Откатить миграцию
venv\Scripts\python -m alembic downgrade -1
```

### Тестирование и качество кода
```bash
# Запуск тестов
venv\Scripts\python -m pytest

# Форматирование кода
venv\Scripts\python -m black app/
venv\Scripts\python -m isort app/

# Проверка стиля
venv\Scripts\python -m flake8 app/
```

## 📁 Структура для разработки

```
ITBase-/
├── app/                    # Основной код приложения
├── venv/                   # Виртуальное окружение
├── .env                    # Настройки (создается автоматически)
├── run_dev.py             # Скрипт запуска для разработки
├── setup_dev.py           # Скрипт настройки проекта
├── run.bat / run.sh       # Быстрый запуск
└── Makefile.dev           # Команды для разработки
```

## 🔧 Решение проблем

### Проблема: "ModuleNotFoundError"
```bash
# Переустановите зависимости
python run_dev.py --install
```

### Проблема: "Can't connect to database"
1. Убедитесь, что PostgreSQL запущен
2. Проверьте настройки в `.env` файле
3. Проверьте доступность базы данных:
   ```bash
   # Windows
   telnet 10.20.30.40 5432
   
   # Linux/Mac
   nc -zv 10.20.30.40 5432
   ```

### Проблема: "Permission denied"
```bash
# Linux/Mac - дайте права на выполнение
chmod +x run.sh
chmod +x setup_dev.py
```

## 🌐 Доступ к приложению

После успешного запуска:
- **Основное приложение**: http://localhost:8000
- **Документация API**: http://localhost:8000/docs
- **ReDoc документация**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

## 📝 Фиксация рабочего состояния

### Git коммит
```bash
git add .
git commit -m "feat: упрощение разработки - добавлены скрипты setup_dev.py и run_dev.py"
git push
```

### Создание тега версии
```bash
git tag -a v1.0.0-dev -m "Рабочая версия для разработки"
git push origin v1.0.0-dev
```

### Экспорт зависимостей
```bash
# Обновить requirements
venv\Scripts\pip freeze > requirements.txt
```

## 🎯 Следующие шаги для упрощения

1. **Добавить Docker Compose для разработки** - изолированная база данных
2. **Настроить hot-reload** - автоматическая перезагрузка при изменениях
3. **Добавить pre-commit hooks** - автоматическая проверка кода
4. **Создать тестовые данные** - быстрое заполнение базы для тестирования
5. **Добавить логирование** - удобная отладка

## 💡 Рекомендации

- Используйте виртуальное окружение для изоляции зависимостей
- Регулярно делайте коммиты с описательными сообщениями
- Тестируйте изменения перед коммитом
- Следите за обновлениями зависимостей