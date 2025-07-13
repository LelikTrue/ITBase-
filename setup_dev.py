#!/usr/bin/env python3
"""
Скрипт для первоначальной настройки проекта в режиме разработки
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_venv():
    """Создает виртуальное окружение"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Виртуальное окружение уже существует")
        return True
    
    print("🔧 Создание виртуального окружения...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Виртуальное окружение создано")
        return True
    except subprocess.CalledProcessError:
        print("❌ Ошибка при создании виртуального окружения")
        return False

def setup_env_file():
    """Настраивает .env файл"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ Файл .env уже существует")
        return True
    
    if not env_example.exists():
        print("❌ Файл .env.example не найден")
        return False
    
    print("📝 Создание .env файла из примера...")
    try:
        shutil.copy(env_example, env_file)
        print("✅ Файл .env создан")
        print("⚠️  Не забудьте настроить переменные в .env файле!")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании .env файла: {e}")
        return False

def install_dependencies():
    """Устанавливает зависимости"""
    print("📦 Установка зависимостей...")
    
    # Определяем путь к pip в виртуальном окружении
    if os.name == 'nt':  # Windows
        pip_path = Path("venv/Scripts/pip.exe")
        python_path = Path("venv/Scripts/python.exe")
    else:  # Linux/Mac
        pip_path = Path("venv/bin/pip")
        python_path = Path("venv/bin/python")
    
    if not pip_path.exists():
        print("❌ pip не найден в виртуальном окружении")
        return False
    
    try:
        # Обн��вляем pip
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Устанавливаем зависимости для разработки
        subprocess.run([str(python_path), "-m", "pip", "install", "-r", "requirements/dev.txt"], check=True)
        
        print("✅ Зависимости установлены успешно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False

def create_run_script():
    """Создает удобный скрипт запуска"""
    if os.name == 'nt':  # Windows
        script_content = '''@echo off
echo 🚀 Запуск ITBase в режиме разработки...
call venv\\Scripts\\activate
python run_dev.py
pause
'''
        script_path = Path("run.bat")
    else:  # Linux/Mac
        script_content = '''#!/bin/bash
echo "🚀 Запуск ITBase в режиме разработки..."
source venv/bin/activate
python run_dev.py
'''
        script_path = Path("run.sh")
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if os.name != 'nt':
            os.chmod(script_path, 0o755)
        
        print(f"✅ Создан скрипт запуска: {script_path}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании скрипта: {e}")
        return False

def print_next_steps():
    """Выводит следующие шаги"""
    print("\n" + "=" * 50)
    print("🎉 Настройка завершена!")
    print("=" * 50)
    print("\n📋 Следующие шаги:")
    print("1. Настройте переменные в файле .env")
    print("2. Убедитесь, что PostgreSQL запущен и доступен")
    print("3. Запустите приложение:")
    
    if os.name == 'nt':
        print("   - Двойной клик на run.bat")
        print("   - Или: venv\\Scripts\\activate && python run_dev.py")
    else:
        print("   - ./run.sh")
        print("   - Или: source venv/bin/activate && python run_dev.py")
    
    print("\n🌐 После запуска приложение будет доступно:")
    print("   - Основное приложение: http://localhost:8000")
    print("   - Документация API: http://localhost:8000/docs")
    print("\n💡 Полезные команды:")
    print("   - python run_dev.py --install  # Переустановить зависимости")
    print("   - python run_dev.py --migrate  # Применить миграции")

def main():
    """Основная функция"""
    print("🔧 ITBase - Настройка проекта для разработки")
    print("=" * 50)
    
    # Проверяем, что мы в правильной директории
    if not Path("app").exists() or not Path("requirements").exists():
        print("❌ Запустите скрипт из корневой директории проекта ITBase")
        return 1
    
    # Создаем виртуальное окружение
    if not create_venv():
        return 1
    
    # Настраиваем .env файл
    if not setup_env_file():
        return 1
    
    # Устанавливаем зависимости
    if not install_dependencies():
        return 1
    
    # Создаем скрипт запуска
    create_run_script()
    
    # Выводим следующие шаги
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())