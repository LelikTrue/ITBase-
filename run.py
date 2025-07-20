#!/usr/bin/env python3
"""
Универсальный скрипт для запуска приложения в режиме разработки.

Использование:
  python run.py [команды]

Команды:
  --install      : Установить/обновить зависимости из requirements/dev.txt
  --migrate      : Применить миграции базы данных (alembic upgrade head)
  --init-data    : Заполнить базу данных начальными данными (запускает init_data.py)
  --no-emoji     : Запустить скрипт без использования эмодзи в выводе
"""
import sys
import subprocess
from pathlib import Path

def get_icons(no_emoji=False):
    """Возвращает словарь с иконками (эмодзи или текстовые)"""
    if no_emoji or sys.platform == "win32":
        return {"ok": "[+]", "error": "[!]", "info": "[i]", "warn": "[?]", "run": "[>]"}
    return {"ok": "✅", "error": "❌", "info": "📝", "warn": "⚠️", "run": "🚀"}

def check_venv(icons):
    """Проверяет, активировано ли виртуальное окружение"""
    is_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not is_venv:
        print(f"{icons['warn']} Виртуальное окружение не активировано.")
        print(f"{icons['info']} Рекомендуется использовать виртуальное окружение:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   source venv/bin/activate  # Linux/Mac")
        print()
    return is_venv

def check_env_file(icons):
    """Проверяет наличие .env файла"""
    if not Path('.env').exists():
        print(f"{icons['error']} Файл .env не найден!")
        print(f"{icons['info']} Создайте файл .env на основе .env.example:")
        print("   cp .env.example .env")
        return False
    return True

def run_command(command, success_msg, error_msg, icons):
    """Универсальная функция для запуска команд"""
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print(f"{icons['ok']} {success_msg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{icons['error']} {error_msg}")
        print(f"--- STDOUT ---\n{e.stdout}")
        print(f"--- STDERR ---\n{e.stderr}")
        return False

def start_server(icons):
    """Запускает сервер разработки"""
    print(f"{icons['run']} Запуск сервера разработки...")
    print(f"    Приложение будет доступно по адресу: http://localhost:8000")
    print(f"    Документация API: http://localhost:8000/docs")
    print(f"{icons['info']} Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print(f"\n{icons['warn']} Сервер остановлен.")
    except subprocess.CalledProcessError:
        print(f"{icons['error']} Ошибка при запуске сервера.")

def main():
    """Основная функция"""
    args = set(sys.argv[1:])
    no_emoji = '--no-emoji' in args
    icons = get_icons(no_emoji)

    print("ITBase - Запуск в режиме разработки")
    print("=" * 50)
    
    check_venv(icons)
    
    if not check_env_file(icons):
        return 1
    
    # Установка зависимостей
    if "--install" in args:
        print("Установка зависимостей...")
        if not run_command(
            [sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt"],
            "Зависимости установлены/обновлены.",
            "Ошибка при установке зависимостей.",
            icons
        ):
            return 1
    
    # Применение миграций
    if "--migrate" in args:
        print("Применение миграций...")
        if not run_command(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            "Миграции успешно применены.",
            "Ошибка при применении миграций (возможно, БД недоступна).",
            icons
        ):
            print(f"{icons['warn']} Продолжаем без миграций...")

    # Инициализация базы данных
    if "--init-data" in args:
        print("Инициализация базы данных...")
        if not run_command(
            [sys.executable, "init_data.py"],
            "База данных успешно инициализирована.",
            "Ошибка при инициализации базы данных.",
            icons
        ):
            print(f"{icons['warn']} Продолжаем без инициализации данных...")

    # Запуск сервера
    start_server(icons)
    return 0

if __name__ == "__main__":
    sys.exit(main())