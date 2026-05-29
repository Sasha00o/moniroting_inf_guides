# 🤖 AI Monitor Bot - Telegram бот для мониторинга инфоповодов

Автоматизированная система для мониторинга новостей/инфоповодов по разным географическим регионам и генерации маркетинговых идей через AI.

## ✨ Возможности

- 🌍 **Мультирегиональный мониторинг** - поддержка 20+ стран (BR, MX, AR, IN, PH и другие)
- 🤖 **AI анализ** - поддержка нескольких провайдеров:
  - Google Gemini (бесплатно, 15 req/min)
  - Anthropic Claude (бесплатно)
  - OpenAI GPT-4 (платно, высокое качество)
  - Groq (бесплатно, быстрый)
- 📊 **Автоматическая генерация отчетов** в Google Sheets с 6 блоками:
  1. Сырые инфоповоды (10-20)
  2. Углы и идеи (20-30)
  3. Рекламные заголовки (30-50)
  4. Топ-5 рекомендаций
  5. Анализ рисков
  6. Доска срочности
- 📅 **Расписание** - автоматический запуск по расписанию (каждые 3-4 дня)
- 💬 **Telegram интеграция** - полный контроль через бота
- 📰 **Агрегация новостей** из Google News и локальных RSS лент

## 🚀 Быстрый старт (5 минут)

### ⚡ Минимальная проверка (тест AI)

Просто проверить, работает ли AI провайдер:

```bash
# 1. Установи зависимости
pip install -r requirements.txt

# 2. Скопируй конфиг
cp .env.example .env

# 3. Заполни ТОЛЬКО AI ключ в .env:
# AI_PROVIDER=groq
# GROQ_API_KEY=gsk_xxxxxxx

# 4. Запусти тест AI
python test_ai_agent.py
```

✅ Если вывод показал результат AI - все работает!

---

### 🔧 Полная установка (Telegram бот)

#### 1. Требования
- Python 3.11+
- Telegram Bot Token (получи в [@BotFather](https://t.me/botfather))
- API ключ одного из AI провайдеров:
  - **Groq** (бесплатно, быстро) 👈 рекомендуется
  - Google Gemini (бесплатно)
  - Anthropic Claude (бесплатно)
  - OpenAI GPT-4 (платно)
- Опционально: Google Service Account для Google Sheets

#### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

#### 3. Конфигурация

**На Windows (PowerShell/CMD):**
```batch
copy .env.example .env
# Отредактируй .env в блокноте
```

**На Linux/Mac:**
```bash
cp .env.example .env
nano .env
```

**Заполни в `.env`:**

```ini
# ⭐ ОБЯЗАТЕЛЬНЫЕ
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ  # От @BotFather
ADMIN_USER_IDS=123456789  # Твой ID (получи от @userinfobot)
AI_PROVIDER=groq

# ⭐ Один из них
GROQ_API_KEY=gsk_xxxxxxx  # https://console.groq.com
# GEMINI_API_KEY=AIza...   # https://ai.google.dev
# CLAUDE_API_KEY=sk-ant-... # https://console.anthropic.com
# OPENAI_API_KEY=sk-... # https://platform.openai.com

# 📊 Для Google Sheets (опционально)
GOOGLE_DRIVE_FOLDER_ID=1abc...xyz
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google_service_account.json

# Остальное (можно оставить по умолчанию)
MODE=DEV
SCHEDULE_CRON=0 9 */3 * *
```

#### 4. Google Sheets (опционально)

Если нужны автоматические отчеты в Google Sheets:

1. Открой [Google Cloud Console](https://console.cloud.google.com/)
2. Создай новый проект
3. Включи API: **Google Sheets API** + **Google Drive API**
4. Создай **Service Account** и скачай JSON
5. Помести файл: `credentials/google_service_account.json`
6. Создай папку в Google Drive и поделись ей с email из JSON

#### 5. Запуск Telegram бота

```bash
# Windows
run.bat

# Linux/Mac
bash run.sh

# Или прямо
python main.py
```

✅ Когда увидишь `🚀 Запуск бота` - бот готов!

Отправь ему `/start` в Telegram.

#### 6. Команды бота

| Команда | Описание |
|---------|---------|
| `/start` | Главное меню |
| `/help` | Справка |
| `/generate BR` | Генерировать отчет для Бразилии |
| `/status` | Статус генераций |
| `/geos` | Список стран |
| `/cancel` | Отмена |

---

### 🐛 Решение проблем

**Python не найден:**
```bash
# Убедись что Python 3.11+ установлен
python --version

# Если не работает, установи Python:
# https://www.python.org (отметь "Add to PATH")
```

**Ошибка API ключа:**
- Проверь что ключ скопирован полностью без пробелов
- Убедись что .env в кодировке UTF-8

**Telegram бот не отвечает:**
- Проверь что токен скопирован правильно
- Перезагрузи бота: отправь `/start`

## 📋 Команды Telegram бота

| Команда | Описание |
|---------|---------|
| `/start` | Главное меню |
| `/help` | Справка по командам |
| `/generate [GEO]` | Генерировать отчет (например `/generate BR`) |
| `/status` | Статус активных генераций |
| `/geos` | Список поддерживаемых стран |
| `/cancel` | Отменить текущую генерацию |

## 🌍 Поддерживаемые страны

### Латинская Америка
- 🇦🇷 Argentina (AR)
- 🇧🇷 Brazil (BR)
- 🇨🇱 Chile (CL)
- 🇨🇴 Colombia (CO)
- 🇲🇽 Mexico (MX)
- 🇵🇪 Peru (PE)
- 🇻🇪 Venezuela (VE)
- И другие...

### Азия
- 🇮🇳 India (IN)
- 🇮🇩 Indonesia (ID)
- 🇵🇭 Philippines (PH)
- 🇹🇭 Thailand (TH)
- 🇻🇳 Vietnam (VN)
- И другие...

### Африка
- 🇳🇬 Nigeria (NG)
- 🇿🇦 South Africa (ZA)
- 🇰🇪 Kenya (KE)

## 🏗️ Архитектура

```
┌─────────────────┐
│  Telegram Bot   │ ← Команды пользователя (/generate BR, /status, /help)
│    (aiogram)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Bot Handlers   │ ← Маршрутизация команд, взаимодействие с пользователем
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Report Generator │ ← Главная логика оркестрации
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌─────┐  ┌──────┐  ┌──────────┐
│ News   │ │ AI  │  │Google│  │Scheduler │
│Parsers │ │Agent│  │Sheets│  │(APScheduler)│
└────────┘ └─────┘  └──────┘  └──────────┘
```

### Структура проекта

```
moniroting_inf_guides/
├── main.py                          # Точка входа бота
├── config.py                        # Конфигурация
├── requirements.txt                 # Зависимости
├── .env                             # Переменные окружения (не коммитить!)
├── .env.example                     # Шаблон .env
├── credentials/
│   └── google_service_account.json   # Google API ключ
├── logs/                            # Логи (автоматически создается)
├── bot/
│   ├── __init__.py
│   ├── handlers.py                  # Обработчики команд Telegram
│   ├── keyboards.py                 # Inline клавиатуры
│   └── middlewares.py               # Логирование, обработка ошибок
├── core/
│   ├── __init__.py
│   ├── report_generator.py          # Главная оркестрация генерации
│   ├── ai_agent.py                  # Обертка для AI API
│   ├── news_parser.py               # Сбор новостей из источников
│   └── scheduler.py                 # APScheduler интеграция
├── database/
│   ├── __init__.py
│   ├── sheets_manager.py            # CRUD для Google Sheets
│   └── models.py                    # Структуры данных (dataclasses)
└── utils/
    ├── __init__.py
    ├── logger.py                    # Логирование (loguru)
    └── helpers.py                   # Вспомогательные функции
```

## 🔄 Процесс генерации отчета

1. **Парсинг новостей** (10%) - сбор из Google News и RSS лент
2. **Классификация** (40%) - AI анализирует новости → инфоповоды
3. **Генерация углов** (60%) - создание маркетинговых углов
4. **Заголовки** (75%) - рекламные заголовки в разных форматах
5. **Риски** (85%) - анализ юридических и других рисков
6. **Приоритизация** (93%) - выбор топ-5 идей для теста
7. **Google Sheets** (100%) - запись всех блоков в отчет

Каждый этап можно отследить в Telegram!

## 📊 Структура отчета Google Sheets

### Шапка
- GEO, дата генерации, период покрытия, ответственный

### Блок 1: Сырые инфоповоды (10-20 шт)
| Заголовок | Источник | Дата | Категория | Описание | Триггер | Срочность |
|-----------|----------|------|-----------|---------|---------|-----------|

### Блок 2: Углы и идеи (20-30 шт)
| ID | Инфоповод | Угол | Связь с офером | Боль | Тип | Приоритет |
|----|-----------|------|---|---|---|---|

### Блок 3: Заголовки (30-50 шт)
| Заголовок | Идея # | Формат | Длина |
|-----------|--------|--------|-------|

### Блок 4: Топ-5 рекомендаций
| Ранг | Идея # | Обоснование | Свежесть | Триггер |
|-----|--------|---|---|---|

### Блок 5: Риски
| Инфоповод # | Юридический | Бан платформой | Негатив аудитории | Срок |
|---|---|---|---|---|

### Блок 6: Срочность
- 🔥 Срочно (24-48ч)
- ⏳ Можно позже (вечные темы)

## 🛠️ Разработка

### Тестирование

```bash
# Тест AI агента
python test_ai_agent.py

# Тест Claude API
python test_claude_api.py

# Тест Mock AI (без реальных API вызовов)
python test_mock_ai.py
```

### Добавление новой страны

Добавь в `utils/helpers.py` в `GEO_REGISTRY`:

```python
"XX": {
    "name": "Страна",
    "flag": "🇽🇽",
    "gl": "XX",
    "hl": "xx-XX",
    "locale": "xx_XX"
}
```

### Изменение расписания

Отредактируй `SCHEDULE_CRON` в `.env` (CRON формат):

```
minute (0-59)
hour   (0-23)
day    (1-31)
month  (1-12)
day_of_week (0-6, где 0 = понедельник)

*/3 = каждые 3 единицы

Примеры:
0 9 */3 * *     = каждые 3 дня в 9:00
0 9 * * 1       = каждый понедельник в 9:00
0 9 1 * *       = 1-го числа каждого месяца в 9:00
0 9,15,21 * * * = в 9:00, 15:00 и 21:00 каждый день
```

## 📝 Логирование

Все логи хранятся в папке `logs/`:

- `app.log` - общие логи
- `bot.log` - логи Telegram бота
- `ai.log` - логи AI агента
- `sheets.log` - логи Google Sheets
- `news.log` - логи парсера новостей
- `generator.log` - логи генератора отчетов
- `scheduler.log` - логи планировщика
- `errors.log` - ошибки

## 🔐 Безопасность

1. **Не коммитиме .env!** Используй `.gitignore`
2. **Не коммитиме credentials JSON!** 
3. **API ключи** хранятся только в .env
4. **Доступ к боту** ограничен ADMIN_USER_IDS

## 🐛 Troubleshooting

### Ошибка: "GOOGLE_SERVICE_ACCOUNT_FILE not found"

```bash
# Проверь что файл существует
ls -la credentials/google_service_account.json

# И путь в .env правильный
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google_service_account.json
```

### Ошибка: "API key invalid"

- Проверь что ключ скопирован правильно в .env
- Убедись что API включен в Google Cloud Console
- Для Groq: https://console.groq.com/keys
- Для Gemini: https://aistudio.google.com/app/apikey
- Для OpenAI: https://platform.openai.com/api-keys
- Для Claude: https://console.anthropic.com

### Ошибка: "GEO not supported"

```bash
# Проверь доступные GEO в боте
/geos

# Или в коде
utils/helpers.py → GEO_REGISTRY
```

### Бот не отвечает

```bash
# Проверь логи
tail -f logs/bot.log

# Проверь что токен правильный
echo $TELEGRAM_BOT_TOKEN

# Попробуй перезапустить
python main.py
```

## 📚 Дополнительные ресурсы

- [Aiogram документация](https://docs.aiogram.dev/)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [APScheduler документация](https://apscheduler.readthedocs.io/)
- [Loguru документация](https://loguru.readthedocs.io/)

## 💡 Tips & Tricks

### Ускорить генерацию

Используй **Groq** вместо других провайдеров - он быстрее всех:
```ini
AI_PROVIDER=groq
GROQ_API_KEY=your_key
```

### Больше инфоповодов

В `config.py` измени лимиты:
```python
INFOREASONS_MIN: int = 15  # вместо 10
INFOREASONS_MAX: int = 30  # вместо 20
```

### Лучше промпты

Отредактируй системные промпты в `core/ai_agent.py` методах `classify_inforeasons()`, `generate_angles()` и т.д.

### Своя база новостей

Добавь RSS ленты в `RSS_FEEDS` в `core/news_parser.py`

## 📞 Поддержка

Если возникли проблемы:

1. Проверь логи в `logs/`
2. Посмотри на ошибку подробнее
3. Убедись что все API ключи актуальны
4. Попробуй обновить requirements.txt

## 📄 Лицензия

MIT License - используй свободно!

---

**Автор:** AI Assistant  
**Версия:** 1.0  
**Последний обновление:** 2026-05-29
