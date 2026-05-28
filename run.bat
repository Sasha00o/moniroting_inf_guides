@echo off
REM 🚀 Скрипт быстрого запуска AI Monitor Bot (Windows)

echo ================================================
echo 🚀 AI Monitor Bot - Быстрый старт (Windows)
echo ================================================
echo.

REM Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не установлен или не добавлен в PATH
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python найден: %PYTHON_VERSION%
echo.

REM Установка зависимостей
echo 📦 Установка зависимостей...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Ошибка установки зависимостей
    exit /b 1
)
echo ✅ Зависимости установлены
echo.

REM Проверка .env
if not exist ".env" (
    echo ⚠️  Файл .env не найден
    echo 📋 Создаю .env из .env.example...
    copy .env.example .env
    echo.
    echo ❌ ВНИМАНИЕ: Отредактируй .env перед запуском!
    echo    - TELEGRAM_BOT_TOKEN
    echo    - ADMIN_USER_IDS
    echo    - AI_PROVIDER и соответствующий API ключ
    echo.
    pause
    exit /b 1
)

REM Проверка обязательных переменных
findstr /m "TELEGRAM_BOT_TOKEN" .env >nul
if %errorlevel% neq 0 (
    echo ❌ TELEGRAM_BOT_TOKEN не установлен в .env
    pause
    exit /b 1
)

findstr /m "AI_PROVIDER" .env >nul
if %errorlevel% neq 0 (
    echo ❌ AI_PROVIDER не установлен в .env
    pause
    exit /b 1
)

echo ✅ Конфигурация проверена
echo.

REM Создание папки логов
if not exist "logs" mkdir logs
echo 📁 Папка логов создана
echo.

REM Запуск бота
echo 🤖 Запуск бота...
echo.
python main.py
pause
