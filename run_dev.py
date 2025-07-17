#!/usr/bin/env python3
"""
Простой скрипт для запуска приложения в режиме разработки
"""
import os
import sys
import subprocess
from pathlib import Path

def check_venv():
    """Проверяет, активировано ли виртуальное окружение"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def check_env_file():
    """Проверяет наличие .env файла"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Файл .env не найден!")
        print("📝 Создайте файл .env на основе .env.example:")
        print("   cp .env.example .env")
        return False
    return True

def install_dependencies():
    """Устанавливает зависимости"""
    print("📦 Установка зависимостей...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt"], check=True)
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка при установке зависимостей")
        return False

def run_migrations():
    """Запускает миграции базы данных"""
    print("🔄 Применение миграций...")
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
        print("✅ Миграции применены успешно")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Ошибка при применении миграций (возможно, база данных недоступна)")
        return False

def init_database():
    """Инициализирует базу данных начальными данными"""
    print("🗄️  Инициализация базы данных...")
    try:
        subprocess.run([sys.executable, "init_data.py"], check=True)
        print("✅ База данных инициализирована")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка при инициализации базы данных")
        return False

def start_server():
    """Запускает сервер разработки"""
    print("🚀 Запуск сервера разработки...")
    print("📍 Приложение будет доступно по адресу: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("🛑 Для остановки нажмите Ctrl+C")
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
        print("\nСервер остановлен")
    except subprocess.CalledProcessError:
        print("Ошибка при запуске сервера")

def main():
    """Основная функция"""
    print("ITBase - Запуск в режиме разработки")
    print("=" * 50)
    
    # Проверяем виртуальное окружение
    if not check_venv():
        print("[!] Виртуальное окружение не активировано")
        print("[i] Рекомендуется использовать виртуальное окружение:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   source venv/bin/activate  # Linux/Mac")
        print()
    
    # Проверяем .env файл
    if not check_env_file():
        return 1
    
    # Устанавливаем зависимости
    if "--install" in sys.argv or not Path("venv").exists():
        if not install_dependencies():
            return 1
    
    # Применяем ми��рации
    if "--migrate" in sys.argv:
        if not run_migrations():
            print("⚠️  Продолжаем без миграций...")
    
    # Инициализируем базу данных
    if "--init-data" in sys.argv:
        if not init_database():
            print("⚠️  Продолжаем без инициализации данных...")
    
    # Запускаем сервер
    start_server()
    return 0

if __name__ == "__main__":
    sys.exit(main())