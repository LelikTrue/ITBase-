#!/usr/bin/env python3
"""
Простой скрипт для запуска приложения в режиме разработки (без эмодзи для Windows)
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
        print("[!] Файл .env не найден!")
        print("[i] Создайте файл .env на основе .env.example:")
        print("   cp .env.example .env")
        return False
    return True

def start_server():
    """Запускает сервер разработки"""
    print("[*] Запуск сервера разработки...")
    print("[i] Приложение будет доступно по адресу: http://localhost:8000")
    print("[i] Документация API: http://localhost:8000/docs")
    print("[i] Для остановки нажмите Ctrl+C")
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
        print("\n[!] Сервер остановлен")
    except subprocess.CalledProcessError:
        print("[!] Ошибка при запуске сервера")

def main():
    """Основная функция"""
    print("[*] ITBase - Запуск в режиме разработки")
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
    
    # Запускаем сервер
    start_server()
    return 0

if __name__ == "__main__":
    sys.exit(main())
