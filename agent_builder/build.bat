@echo off
chcp 65001 >nul
cls

echo ==========================================
echo   Сборщик Агента ITBase (Windows)
echo ==========================================

:: 1. Проверка, что мы на Windows
if "%OS%"=="" (
    echo [ERROR] Этот скрипт предназначен только для Windows!
    exit /b 1
)

:: 2. Создание временного виртуального окружения для сборки
echo [1/5] Создание виртуального окружения...
if not exist "agent_venv" (
    python -m venv agent_venv
)

:: 3. Активация и установка зависимостей
echo [2/5] Установка библиотек (PyInstaller, WMI)...
call agent_venv\Scripts\activate
pip install -r src\requirements.txt --disable-pip-version-check --quiet

:: 4. Сборка EXE
echo [3/5] Компиляция EXE файла...
:: --onefile: один файл
:: --noconsole: (ОПЦИОНАЛЬНО) уберите этот флаг, если хотите видеть консоль при запуске агента
:: --distpath: куда положить итог (в корень папки agent_builder)
:: --workpath: временная папка
:: --specpath: временная папка
pyinstaller --noconfirm --onefile --name "ITBase_Agent" --distpath "." --workpath "agent_build_temp" --specpath "agent_build_temp" src/agent.py

:: 5. Очистка
echo [4/5] Очистка временных файлов...
deactivate
rmdir /s /q agent_venv
rmdir /s /q agent_build_temp

echo.
echo ==========================================
echo [SUCCESS] Готово! Файл ITBase_Agent.exe создан.
echo ==========================================
pause
