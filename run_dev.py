#!/usr/bin/env python3
"""
Основной скрипт для запуска и управления приложением в режиме разработки.
"""

import argparse
import os
import subprocess
import sys

try:
    from dotenv import load_dotenv

    print("✅ Переменные окружения из .env загружены.")
    load_dotenv()
except ImportError:
    print(
        "⚠️  Warning: `python-dotenv` не установлен. Переменные из .env не будут загружены."
    )


def run_command(command, description):
    """Выполняет команду в терминале и проверяет результат."""
    print(f"🚀 Выполнение: {description}...")
    try:
        subprocess.run([sys.executable, "-m"] + command, check=True)
        print(f"✅ Успешно: {description}.")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"❌ Ошибка при выполнении: {description}.")
        return False


def start_server():
    """Запускает сервер разработки Uvicorn через subprocess для надежности."""
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("APP_PORT", "8000")
    app_location = "app.main:app"

    display_host = "localhost" if host == "0.0.0.0" else host

    print("\n" + "=" * 50)
    print("🦄 Запуск сервера разработки Uvicorn...")
    print(f"   - Приложение: http://{display_host}:{port}")
    print(f"   - Документация API: http://{display_host}:{port}/docs")
    print("   - Для остановки нажмите Ctrl+C")
    print("=" * 50 + "\n")

    try:
        # Этот метод гарантирует, что uvicorn и его дочерний процесс
        # (для --reload) будут запущены с использованием python.exe из текущего venv.
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                app_location,
                "--reload",
                "--host",
                host,
                "--port",
                port,
                "--log-level",
                "info",
            ],
            check=True,
        )

    except KeyboardInterrupt:
        print("\n[!] Сервер остановлен.")
    except subprocess.CalledProcessError:
        print("\n[!] Ошибка при запуске сервера.")


def main():
    """Основная функция: парсит аргументы и выполняет действия."""
    parser = argparse.ArgumentParser(
        description="Скрипт запуска ITBase в режиме разработки."
    )
    parser.add_argument(
        "--install", action="store_true", help="Установить/обновить зависимости"
    )
    parser.add_argument(
        "--migrate", action="store_true", help="Применить миграции базы данных"
    )
    args = parser.parse_args()

    if args.install:
        if not run_command(
            ["pip", "install", "-r", "requirements/dev.txt"], "Установка зависимостей"
        ):
            sys.exit(1)

    if args.migrate:
        if not run_command(["alembic", "upgrade", "head"], "Применение миграций"):
            sys.exit(1)

    start_server()


if __name__ == "__main__":
    main()
