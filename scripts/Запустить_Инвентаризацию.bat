@echo off
chcp 65001 >nul
cls

:: ==========================================
:: ITBase Inventory Launcher
:: ==========================================

echo Запуск агента инвентаризации...
echo.

:: Переходим в директорию, где лежит этот батник (чтобы найти ps1)
cd /d "%~dp0"

:: Проверка наличия скрипта
if not exist "Agent.ps1" (
    color 0C
    echo [ОШИБКА] Файл Agent.ps1 не найден!
    echo Убедитесь, что Agent.ps1 и этот файл находятся в одной папке.
    echo.
    pause
    exit /b
)

:: Запуск PowerShell с обходом политик безопасности
:: -NoProfile: не грузить профиль пользователя (быстрее)
:: -ExecutionPolicy Bypass: разрешить скрипт (только этот)
:: -File: путь к файлу
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "Agent.ps1"

echo.
echo ==========================================
echo Сбор данных завершен.
echo Файл components.json создан в этой папке.
echo Вы можете закрыть это окно.
echo ==========================================
pause