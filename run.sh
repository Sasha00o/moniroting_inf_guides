#!/bin/bash

# 🚀 Скрипт быстрого запуска AI Monitor Bot

echo "================================================"
echo "🚀 AI Monitor Bot - Быстрый старт"
echo "================================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен"
    exit 1
fi

echo "✅ Python найден: $(python3 --version)"
echo ""

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Ошибка установки зависимостей"
    exit 1
fi
echo "✅ Зависимости установлены"
echo ""

# Проверка .env
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден"
    echo "📋 Создаю .env из .env.example..."
    cp .env.example .env
    echo ""
    echo "❌ ВНИМАНИЕ: Отредактируй .env перед запуском!"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - ADMIN_USER_IDS"
    echo "   - AI_PROVIDER и соответствующий API ключ"
    echo ""
    exit 1
fi

# Проверка обязательных переменных
if ! grep -q "TELEGRAM_BOT_TOKEN" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен в .env"
    exit 1
fi

if ! grep -q "AI_PROVIDER" .env; then
    echo "❌ AI_PROVIDER не установлен в .env"
    exit 1
fi

echo "✅ Конфигурация проверена"
echo ""

# Создание папки логов
mkdir -p logs
echo "📁 Папка логов создана"
echo ""

# Запуск бота
echo "🤖 Запуск бота..."
echo ""
python3 main.py
