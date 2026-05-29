# 🤖 AI Monitor Bot - Telegram бот для мониторинга инфоповодов

Автоматизированная система для мониторинга новостей/инфоповодов по разным географическим регионам и генерации маркетинговых идей через AI.

## 📖 Что делает проект?

Бот автоматически:
1. **Собирает новости** из Google News по выбранной стране (BR, MX, AR, IN и др.)
2. **Анализирует через AI** и выбирает самые сильные инфоповоды для маркетинга
3. **Генерирует маркетинговые углы** - как использовать новость для рекламы
4. **Создает рекламные заголовки** в разных форматах (вопрос, шок, цифра, интрига)
5. **Оценивает риски** - юридические, баны платформ, негатив аудитории
6. **Приоритизирует идеи** - выбирает топ-10 лучших для A/B тестов
7. **Сохраняет все в Google Sheets** - готовый отчет с 6 блоками данных

**Результат:** Полный маркетинговый отчет за 3-5 минут вместо нескольких часов ручной работы.

## ✨ Возможности

- 🌍 **Мультирегиональный мониторинг** - поддержка 30+ стран (Латинская Америка, Азия, Африка)
- 🤖 **AI анализ** - поддержка 6 провайдеров:
  - **OpenAI GPT-4o-mini** (рекомендуется для продакшена, быстрый и качественный)
  - **Google Gemini 2.0 Flash** (бесплатный tier до 1500 req/day)
  - **Anthropic Claude 3.5 Haiku** (быстрый и дешевый)
  - **Groq** (бесплатно, очень быстрый, llama-3.3-70b)
  - **DeepSeek** (дешевый китайский провайдер)
  - **OpenRouter** (агрегатор моделей, есть бесплатные)
- 📊 **Автоматическая генерация отчетов** в Google Sheets с 6 блоками:
  1. Сырые инфоповоды (15-25 шт)
  2. Углы и идеи (30-50 шт)
  3. Рекламные заголовки (50-80 шт)
  4. Топ-10 рекомендаций для теста
  5. Анализ рисков (юридические, баны, репутация)
  6. Доска срочности (24-48ч vs вечные темы)
- 📅 **Расписание** - автоматический запуск по расписанию (по умолчанию каждые 3 дня в 9:00)
- 💬 **Telegram интеграция** - полный контроль через бота
- 📰 **Агрегация новостей** из Google News (до 100 новостей за последние 7 дней)
- 🔐 **Два метода авторизации Google** - OAuth 2.0 (для личного использования) или Service Account (для серверов)

## 🚀 Быстрый старт

### 1️⃣ Требования

- **Python 3.11+** ([скачать](https://www.python.org/downloads/))
- **Telegram Bot Token** - получи в [@BotFather](https://t.me/botfather)
- **Твой Telegram ID** - получи в [@userinfobot](https://t.me/userinfobot)
- **API ключ AI провайдера** (выбери один):
  - **OpenAI** (рекомендуется) - [получить ключ](https://platform.openai.com/api-keys)
  - **Google Gemini** (бесплатно до 1500 req/day) - [получить ключ](https://aistudio.google.com/app/apikey)
  - **Groq** (бесплатно, быстро) - [получить ключ](https://console.groq.com/keys)
  - **Anthropic Claude** - [получить ключ](https://console.anthropic.com)
  - **DeepSeek** - [получить ключ](https://platform.deepseek.com)
  - **OpenRouter** - [получить ключ](https://openrouter.ai/keys)
- **Google Drive** (для сохранения отчетов):
  - Создай папку в Google Drive
  - Скопируй ID папки из URL (часть после `/folders/`)
  - Настрой авторизацию (см. шаг 4)

### 2️⃣ Установка зависимостей

```bash
# Клонируй репозиторий (если еще не сделал)
git clone <your-repo-url>
cd moniroting_inf_guides

# Установи зависимости
pip install -r requirements.txt
```

### 3️⃣ Конфигурация переменных окружения

**Создай файл `.env`:**

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

**Заполни обязательные переменные в `.env`:**

```ini
# ========================================
# ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ
# ========================================

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ
ADMIN_USER_IDS=123456789

# AI Provider (выбери один: openai | gemini | groq | claude | deepseek | openrouter)
AI_PROVIDER=openai

# API ключ выбранного провайдера (заполни только один)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
# GEMINI_API_KEY=AIzaxxxxxxxxxxxxx
# GROQ_API_KEY=gsk_xxxxxxxxxxxxx
# CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
# DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
# OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxx

# Google Drive (для сохранения отчетов)
GOOGLE_DRIVE_FOLDER_ID=1abc...xyz

# ========================================
# ОПЦИОНАЛЬНЫЕ ПЕРЕМЕННЫЕ (можно оставить по умолчанию)
# ========================================

# Режим работы (DEV | TEST | PROD)
MODE=PROD

# Уровень логирования (DEBUG | INFO | WARNING | ERROR)
LOG_LEVEL=INFO

# Расписание автогенерации (cron формат: минута час день месяц день_недели)
# По умолчанию: каждые 3 дня в 9:00
SCHEDULE_CRON=0 9 */3 * *
```

### 4️⃣ Настройка Google Sheets

Проект поддерживает **два метода авторизации** в Google:

#### Вариант А: OAuth 2.0 (рекомендуется для личного использования)

1. Открой [Google Cloud Console](https://console.cloud.google.com/)
2. Создай новый проект или выбери существующий
3. Включи API:
   - **Google Sheets API**
   - **Google Drive API**
4. Создай **OAuth 2.0 Client ID**:
   - Тип приложения: **Desktop app**
   - Скачай JSON файл
5. Сохрани файл как `credentials/oauth_credentials.json`
6. Добавь в `.env`:
   ```ini
   GOOGLE_OAUTH_CREDENTIALS=credentials/oauth_credentials.json
   ```
7. При первом запуске выполни авторизацию:
   ```bash
   python authorize_oauth.py
   ```
   Откроется браузер для авторизации. После успешной авторизации токен сохранится автоматически.

#### Вариант Б: Service Account (для серверов и автоматизации)

1. Открой [Google Cloud Console](https://console.cloud.google.com/)
2. Создай новый проект
3. Включи API: **Google Sheets API** + **Google Drive API**
4. Создай **Service Account**:
   - IAM & Admin → Service Accounts → Create Service Account
   - Скачай JSON ключ
5. Сохрани файл как `credentials/google_service_account.json`
6. Добавь в `.env`:
   ```ini
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google_service_account.json
   ```
7. **Важно:** Открой свою папку в Google Drive и поделись ей с email из JSON файла (поле `client_email`)

**Примечание:** OAuth имеет приоритет. Если указаны оба метода, будет использован OAuth.

### 5️⃣ Запуск бота

```bash
# Windows
python main.py

# Linux/Mac
python3 main.py
```

**Что должно произойти:**
```
🚀 Запуск бота (режим: PROD)
AI провайдер: openai
📅 Планировщик запущен
✅ Бот готов к работе
```

Теперь открой Telegram и отправь боту `/start`

### 6️⃣ Команды бота

| Команда | Описание | Пример |
|---------|----------|--------|
| `/start` | Главное меню с кнопками | `/start` |
| `/help` | Справка по командам | `/help` |
| `/generate <GEO>` | Генерировать отчет для страны | `/generate BR` |
| `/status` | Статус текущей генерации | `/status` |
| `/geos` | Список всех поддерживаемых стран | `/geos` |
| `/cancel` | Отменить текущую генерацию | `/cancel` |

**Пример использования:**
1. Отправь `/generate BR` (для Бразилии)
2. Бот начнет генерацию и будет показывать прогресс:
   - ⏳ Парсинг новостей... (10%)
   - 🤖 Классификация инфоповодов... (40%)
   - 💡 Генерация углов... (60%)
   - ✍️ Создание заголовков... (75%)
   - ⚠️ Оценка рисков... (85%)
   - 🎯 Приоритизация идей... (93%)
   - 📊 Сохранение в Google Sheets... (100%)
3. Получишь ссылку на готовый отчет в Google Sheets

---

## 📋 Описание переменных окружения

### Обязательные переменные

| Переменная | Описание | Где получить | Пример |
|------------|----------|--------------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | [@BotFather](https://t.me/botfather) | `123456789:ABCdef...` |
| `ADMIN_USER_IDS` | ID администраторов (через запятую) | [@userinfobot](https://t.me/userinfobot) | `123456789,987654321` |
| `AI_PROVIDER` | Выбор AI провайдера | - | `openai` / `gemini` / `groq` / `claude` / `deepseek` / `openrouter` |
| `OPENAI_API_KEY` | API ключ OpenAI (если выбран openai) | [platform.openai.com](https://platform.openai.com/api-keys) | `sk-proj-xxx...` |
| `GEMINI_API_KEY` | API ключ Google Gemini (если выбран gemini) | [aistudio.google.com](https://aistudio.google.com/app/apikey) | `AIzaXXX...` |
| `GROQ_API_KEY` | API ключ Groq (если выбран groq) | [console.groq.com](https://console.groq.com/keys) | `gsk_xxx...` |
| `CLAUDE_API_KEY` | API ключ Anthropic (если выбран claude) | [console.anthropic.com](https://console.anthropic.com) | `sk-ant-xxx...` |
| `DEEPSEEK_API_KEY` | API ключ DeepSeek (если выбран deepseek) | [platform.deepseek.com](https://platform.deepseek.com) | `sk-xxx...` |
| `OPENROUTER_API_KEY` | API ключ OpenRouter (если выбран openrouter) | [openrouter.ai](https://openrouter.ai/keys) | `sk-or-xxx...` |
| `GOOGLE_DRIVE_FOLDER_ID` | ID папки в Google Drive для отчетов | Из URL папки: `drive.google.com/drive/folders/[ID]` | `1abc...xyz` |

### Опциональные переменные

| Переменная | Описание | Значение по умолчанию | Возможные значения |
|------------|----------|----------------------|-------------------|
| `MODE` | Режим работы бота | `PROD` | `DEV` / `TEST` / `PROD` |
| `LOG_LEVEL` | Уровень логирования | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `SCHEDULE_CRON` | Расписание автогенерации (cron) | `0 9 */3 * *` | Любой cron формат |
| `GOOGLE_OAUTH_CREDENTIALS` | Путь к OAuth credentials | `None` | `credentials/oauth_credentials.json` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Путь к Service Account JSON | `credentials/google_service_account.json` | Любой путь к JSON |

### Настройки AI моделей (опциональные)

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `OPENAI_MODEL` | Модель OpenAI | `gpt-4o-mini` |
| `OPENAI_MAX_TOKENS` | Макс. токенов ответа OpenAI | `16384` |
| `OPENAI_TEMPERATURE` | Temperature OpenAI | `0.7` |
| `GEMINI_MODEL` | Модель Gemini | `gemini-2.0-flash-exp` |
| `GEMINI_MAX_TOKENS` | Макс. токенов ответа Gemini | `8192` |
| `GEMINI_TEMPERATURE` | Temperature Gemini | `0.7` |
| `GROQ_MODEL` | Модель Groq | `llama-3.3-70b-versatile` |
| `GROQ_MAX_TOKENS` | Макс. токенов ответа Groq | `8192` |
| `GROQ_TEMPERATURE` | Temperature Groq | `0.7` |
| `GROQ_BASE_URL` | Base URL Groq API | `https://api.groq.com/openai/v1` |
| `CLAUDE_MODEL` | Модель Claude | `claude-3-5-haiku-20241022` |
| `CLAUDE_MAX_TOKENS` | Макс. токенов ответа Claude | `4096` |
| `CLAUDE_TEMPERATURE` | Temperature Claude | `0.7` |

### Настройки генерации (опциональные)

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `NEWS_DAYS_BACK` | Сколько дней назад искать новости | `7` |
| `NEWS_MAX_ITEMS` | Макс. количество новостей для парсинга | `100` |
| `INFOREASONS_MIN` | Мин. количество инфоповодов | `15` |
| `INFOREASONS_MAX` | Макс. количество инфоповодов | `25` |
| `ANGLES_MIN` | Мин. количество углов | `30` |
| `ANGLES_MAX` | Макс. количество углов | `50` |
| `HEADLINES_MIN` | Мин. количество заголовков | `50` |
| `HEADLINES_MAX` | Макс. количество заголовков | `80` |
| `TOP_IDEAS_COUNT` | Количество топ-идей для рекомендаций | `10` |

---

## 🌍 Поддерживаемые страны (30+ GEO)

### Латинская Америка (18 стран)
- 🇦🇷 Argentina (AR)
- 🇧🇴 Bolivia (BO)
- 🇧🇷 Brazil (BR)
- 🇨🇱 Chile (CL)
- 🇨🇴 Colombia (CO)
- 🇨🇷 Costa Rica (CR)
- 🇩🇴 Dominican Republic (DO)
- 🇪🇨 Ecuador (EC)
- 🇬🇹 Guatemala (GT)
- 🇭🇳 Honduras (HN)
- 🇲🇽 Mexico (MX)
- 🇳🇮 Nicaragua (NI)
- 🇵🇦 Panama (PA)
- 🇵🇪 Peru (PE)
- 🇵🇾 Paraguay (PY)
- 🇸🇻 El Salvador (SV)
- 🇺🇾 Uruguay (UY)
- 🇻🇪 Venezuela (VE)

### Азия (8 стран)
- 🇮🇳 India (IN)
- 🇮🇩 Indonesia (ID)
- 🇵🇭 Philippines (PH)
- 🇹🇭 Thailand (TH)
- 🇻🇳 Vietnam (VN)
- 🇲🇾 Malaysia (MY)
- 🇸🇬 Singapore (SG)
- 🇵🇰 Pakistan (PK)

### Африка (3 страны)
- 🇳🇬 Nigeria (NG)
- 🇿🇦 South Africa (ZA)
- 🇰🇪 Kenya (KE)

**Добавление новой страны:** см. раздел "Разработка" ниже

---

## 🏗️ Архитектура проекта

### Схема работы

```
┌─────────────────┐
│  Telegram Bot   │ ← Пользователь отправляет команды (/generate BR, /status)
│    (aiogram)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Bot Handlers   │ ← Обработка команд, inline кнопки, middleware
│  (bot/handlers) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Report Generator │ ← Главная оркестрация: координирует все этапы
│(core/report_gen)│
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼          ▼
┌────────┐ ┌─────┐  ┌──────┐  ┌──────────┐ ┌────────┐
│ News   │ │ AI  │  │Google│  │Scheduler │ │ Logger │
│Parser  │ │Agent│  │Sheets│  │(APSched) │ │(loguru)│
└────────┘ └─────┘  └──────┘  └──────────┘ └────────┘
```

### Структура файлов

```
moniroting_inf_guides/
├── main.py                          # 🚀 Точка входа - запуск бота
├── config.py                        # ⚙️ Конфигурация (Pydantic Settings)
├── requirements.txt                 # 📦 Зависимости Python
├── .env                             # 🔐 Переменные окружения (НЕ коммитить!)
├── .env.example                     # 📝 Шаблон .env
├── authorize_oauth.py               # 🔑 Скрипт OAuth авторизации Google
│
├── credentials/                     # 🔐 Ключи доступа
│   ├── oauth_credentials.json       # OAuth 2.0 credentials (НЕ коммитить!)
│   ├── google_service_account.json  # Service Account key (НЕ коммитить!)
│   └── token.json                   # OAuth токен (создается автоматически)
│
├── logs/                            # 📋 Логи (создается автоматически)
│   ├── app.log                      # Общие логи приложения
│   ├── bot.log                      # Логи Telegram бота
│   ├── ai.log                       # Логи AI агента
│   ├── sheets.log                   # Логи Google Sheets
│   ├── news.log                     # Логи парсера новостей
│   ├── generator.log                # Логи генератора отчетов
│   ├── scheduler.log                # Логи планировщика
│   └── errors.log                   # Только ошибки
│
├── bot/                             # 🤖 Telegram бот
│   ├── __init__.py
│   ├── handlers.py                  # Обработчики команд (/start, /generate, etc)
│   ├── keyboards.py                 # Inline клавиатуры
│   └── middlewares.py               # Логирование, обработка ошибок
│
├── core/                            # 🧠 Бизнес-логика
│   ├── __init__.py
│   ├── report_generator.py          # Главная оркестрация генерации отчета
│   ├── ai_agent.py                  # AI агент (классификация, углы, заголовки)
│   ├── news_parser.py               # Парсинг новостей из Google News
│   ├── scheduler.py                 # APScheduler для автозапуска
│   └── mock_ai_agent.py             # Mock AI для тестов без API
│
├── database/                        # 💾 Работа с данными
│   ├── __init__.py
│   ├── sheets_manager.py            # CRUD для Google Sheets
│   └── models.py                    # Dataclasses (InfoReason, Angle, etc)
│
└── utils/                           # 🛠️ Утилиты
    ├── __init__.py
    ├── logger.py                    # Настройка логирования (loguru)
    └── helpers.py                   # GEO_REGISTRY, валидация, retry
```

### Процесс генерации отчета (7 этапов)

1. **Парсинг новостей (10%)** - `news_parser.py`
   - Сбор до 100 новостей из Google News за последние 7 дней
   - Фильтрация по региону (gl/hl параметры)

2. **Классификация инфоповодов (40%)** - `ai_agent.classify_inforeasons()`
   - AI анализирует новости и выбирает 15-25 самых сильных инфоповодов
   - Оценивает эмоциональный триггер, срочность, категорию

3. **Генерация углов (60%)** - `ai_agent.generate_angles()`
   - Создание 30-50 маркетинговых углов (2-3 на инфоповод)
   - Связь с оффером, боль аудитории, тип креатива

4. **Создание заголовков (75%)** - `ai_agent.generate_headlines()`
   - Генерация 50-80 рекламных заголовков (3-5 на угол)
   - Разные форматы: вопрос, шок, цифра, интрига, призыв

5. **Оценка рисков (85%)** - `ai_agent.assess_risks()`
   - Юридические риски, баны платформ, негатив аудитории
   - Срок протухания темы

6. **Приоритизация идей (93%)** - `ai_agent.prioritize_ideas()`
   - Выбор топ-10 идей для A/B тестов
   - Оценка свежести, силы триггера, соответствия офферу

7. **Сохранение в Google Sheets (100%)** - `sheets_manager.py`
   - Создание нового файла в Google Drive
   - Запись всех 6 блоков с форматированием

---

## 📊 Структура отчета Google Sheets

Каждый отчет содержит 6 блоков данных:

### 📌 Шапка отчета
- **GEO:** Страна (например, 🇧🇷 Brazil)
- **Дата генерации:** 2026-05-29
- **Период покрытия:** 2026-05-22 - 2026-05-29 (7 дней)
- **AI провайдер:** OpenAI GPT-4o-mini
- **Ответственный:** @username

### 1️⃣ Блок 1: Сырые инфоповоды (15-25 шт)

| Заголовок | Источник | Дата | Категория | Описание | Триггер | Срочность |
|-----------|----------|------|-----------|----------|---------|-----------|
| Новый закон о налогах | Топовое СМИ | 2026-05-28 | банки-налоги | Правительство вводит... | деньги | срочно 24-48ч |

**Категории:** экономика, политика, соцсети, селеба, скандал, банки-налоги, страхи, технологии, здоровье

**Триггеры:** деньги, кризис, возможность, страх, доверие, FOMO

### 2️⃣ Блок 2: Углы и идеи (30-50 шт)

| ID | Инфоповод | Угол | Связь с офером | Боль | Тип | Приоритет |
|----|-----------|------|----------------|------|-----|-----------|
| 1 | #3 | Новый налог съест 20% дохода... | Кредит поможет сохранить... | Потеря денег | эмоциональный | A |

**Типы креатива:** новостной, эмоциональный, разоблачение, личная история, сравнение

**Приоритет:** A (высокий), B (средний), C (низкий)

### 3️⃣ Блок 3: Рекламные заголовки (50-80 шт)

| Заголовок | Идея # | Формат | Длина |
|-----------|--------|--------|-------|
| Новый налог? Узнай как сэкономить 20% | 1 | вопрос | 42 |
| Шокирующая правда о новом налоге | 1 | шок | 38 |

**Форматы:** вопрос, шок, цифра, цитата, интрига, призыв

**Длина:** 40-80 символов (оптимально для рекламы)

### 4️⃣ Блок 4: Топ-10 рекомендаций для теста

| Ранг | Идея # | Обоснование | Свежесть | Триггер | Соответствие |
|------|--------|-------------|----------|---------|--------------|
| 1 | 5 | Сильный эмоциональный триггер... | 9/10 | 8/10 | 9/10 |

**Оценки:** 1-10 баллов по каждому критерию

### 5️⃣ Блок 5: Анализ рисков

| Инфоповод # | Юридический | Бан платформой | Негатив аудитории | Репутация | Срок |
|-------------|-------------|----------------|-------------------|-----------|------|
| 3 | низкий: не нарушает... | средний: может быть... | низкий | низкий | 2-3 дня |

**Уровни риска:** низкий, средний, высокий + пояснение

### 6️⃣ Блок 6: Доска срочности

**🔥 Срочно (24-48 часов):**
- Инфоповод #3: Новый налог (протухнет через 2 дня)
- Инфоповод #7: Скандал с банком (горячая тема)

**⏳ Можно позже (вечные темы):**
- Инфоповод #12: Рост цен на жилье (долгосрочная тема)
- Инфоповод #15: Проблемы с кредитами (всегда актуально)

---

## 🛠️ Разработка и настройка

### Добавление новой страны

Отредактируй `utils/helpers.py`, добавь в `GEO_REGISTRY`:

```python
"XX": {
    "name": "Название страны",
    "flag": "🇽🇽",
    "gl": "XX",           # Google News country code
    "hl": "xx-XX",        # Google News language code
    "locale": "xx_XX"     # Locale для отображения
}
```

**Примеры:**
- Испаноязычные страны: `"hl": "es-419"` (латиноамериканский испанский)
- Португалия/Бразилия: `"hl": "pt-BR"` или `"hl": "pt-PT"`
- Английский: `"hl": "en-US"`, `"hl": "en-GB"`, `"hl": "en-IN"`

### Изменение расписания автогенерации

Отредактируй `SCHEDULE_CRON` в `.env` (формат cron):

```
┌─────── минута (0-59)
│ ┌───── час (0-23)
│ │ ┌─── день месяца (1-31)
│ │ │ ┌─ месяц (1-12)
│ │ │ │ ┌ день недели (0-6, 0=понедельник)
│ │ │ │ │
* * * * *
```

**Примеры:**

```bash
# Каждые 3 дня в 9:00 (по умолчанию)
SCHEDULE_CRON=0 9 */3 * *

# Каждый понедельник в 9:00
SCHEDULE_CRON=0 9 * * 1

# 1-го числа каждого месяца в 9:00
SCHEDULE_CRON=0 9 1 * *

# Каждый день в 9:00, 15:00 и 21:00
SCHEDULE_CRON=0 9,15,21 * * *

# Каждый час
SCHEDULE_CRON=0 * * * *

# Каждые 6 часов
SCHEDULE_CRON=0 */6 * * *
```

### Настройка лимитов генерации

Отредактируй переменные в `.env`:

```bash
# Количество новостей для парсинга
NEWS_DAYS_BACK=7          # Сколько дней назад искать
NEWS_MAX_ITEMS=100        # Максимум новостей

# Лимиты генерации
INFOREASONS_MIN=15        # Минимум инфоповодов
INFOREASONS_MAX=25        # Максимум инфоповодов
ANGLES_MIN=30             # Минимум углов
ANGLES_MAX=50             # Максимум углов
HEADLINES_MIN=50          # Минимум заголовков
HEADLINES_MAX=80          # Максимум заголовков
TOP_IDEAS_COUNT=10        # Топ-N идей для рекомендаций
```

### Настройка AI моделей

Каждый провайдер имеет свои настройки модели:

```bash
# OpenAI
OPENAI_MODEL=gpt-4o-mini              # или gpt-4o, gpt-4-turbo
OPENAI_MAX_TOKENS=16384
OPENAI_TEMPERATURE=0.7

# Gemini
GEMINI_MODEL=gemini-2.0-flash-exp     # или gemini-1.5-pro
GEMINI_MAX_TOKENS=8192
GEMINI_TEMPERATURE=0.7

# Groq
GROQ_MODEL=llama-3.3-70b-versatile    # или llama-3.1-8b-instant
GROQ_MAX_TOKENS=8192
GROQ_TEMPERATURE=0.7

# Claude
CLAUDE_MODEL=claude-3-5-haiku-20241022  # или claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=4096
CLAUDE_TEMPERATURE=0.7
```

**Temperature:**
- `0.0-0.3` - более детерминированный, точный (для классификации, рисков)
- `0.7-0.9` - более креативный (для углов, заголовков)
- `1.0+` - очень креативный, но может быть непредсказуемым

---

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

## 🐛 Решение проблем

### Python не найден

```bash
# Проверь версию Python
python --version
# или
python3 --version

# Должно быть Python 3.11 или выше
```

**Решение:** Установи Python 3.11+ с [python.org](https://www.python.org/downloads/)
- ✅ Windows: отметь "Add Python to PATH" при установке
- ✅ Linux: `sudo apt install python3.11` или `sudo yum install python3.11`
- ✅ Mac: `brew install python@3.11`

### Ошибка: "No module named 'aiogram'" или другие модули

```bash
# Переустанови зависимости
pip install -r requirements.txt

# Или с указанием Python 3
pip3 install -r requirements.txt
```

### Ошибка: "Invalid API key" или "Authentication failed"

**Причины:**
1. Ключ скопирован неполностью или с пробелами
2. Неправильный провайдер в `AI_PROVIDER`
3. Ключ истек или не активирован

**Решение:**
```bash
# 1. Проверь что ключ в .env без пробелов и кавычек
OPENAI_API_KEY=sk-proj-xxxxx  # ✅ правильно
OPENAI_API_KEY="sk-proj-xxxxx"  # ❌ неправильно (кавычки)
OPENAI_API_KEY= sk-proj-xxxxx  # ❌ неправильно (пробел)

# 2. Проверь что AI_PROVIDER соответствует ключу
AI_PROVIDER=openai  # если используешь OPENAI_API_KEY
AI_PROVIDER=gemini  # если используешь GEMINI_API_KEY

# 3. Проверь что ключ активен на сайте провайдера
```

### Ошибка: "GOOGLE_SERVICE_ACCOUNT_FILE not found"

```bash
# Проверь что файл существует
ls credentials/google_service_account.json

# Проверь путь в .env
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/google_service_account.json
```

**Решение:** Скачай Service Account JSON из Google Cloud Console и помести в `credentials/`

### Ошибка: "Permission denied" при записи в Google Sheets

**Причина:** Service Account не имеет доступа к папке Google Drive

**Решение:**
1. Открой файл `credentials/google_service_account.json`
2. Найди поле `client_email` (например: `my-bot@project.iam.gserviceaccount.com`)
3. Открой папку в Google Drive
4. Нажми "Поделиться" → добавь этот email с правами "Редактор"

### Telegram бот не отвечает

**Проверь:**
```bash
# 1. Токен правильный?
echo $TELEGRAM_BOT_TOKEN  # Linux/Mac
echo %TELEGRAM_BOT_TOKEN%  # Windows

# 2. Бот запущен?
# Должно быть сообщение: "✅ Бот готов к работе"

# 3. Твой ID в ADMIN_USER_IDS?
# Получи ID в @userinfobot и добавь в .env
```

### Ошибка: "Rate limit exceeded"

**Причина:** Превышен лимит запросов к AI провайдеру

**Решение:**
1. Подожди несколько минут
2. Или смени провайдера в `.env`:
   ```bash
   AI_PROVIDER=gemini  # переключись на другой
   GEMINI_API_KEY=твой_ключ
   ```

### Ошибка: "GEO not supported"

```bash
# Проверь список поддерживаемых стран
# В боте: /geos
# Или в коде: utils/helpers.py → GEO_REGISTRY
```

**Решение:** Используй двухбуквенный код страны (BR, MX, AR, IN и т.д.)

### Логи для диагностики

Все логи сохраняются в папке `logs/`:

```bash
# Общие логи
tail -f logs/app.log

# Логи бота
tail -f logs/bot.log

# Логи AI
tail -f logs/ai.log

# Только ошибки
tail -f logs/errors.log

# Windows (PowerShell)
Get-Content logs\app.log -Tail 50 -Wait
```

### Бот падает при запуске

```bash
# Проверь логи на ошибки
cat logs/errors.log

# Проверь что все обязательные переменные заполнены
cat .env | grep -E "TELEGRAM_BOT_TOKEN|ADMIN_USER_IDS|AI_PROVIDER|GOOGLE_DRIVE_FOLDER_ID"
```

---

## 💡 Советы по оптимизации

### Ускорить генерацию

1. **Используй быстрые модели:**
   ```bash
   # Groq - самый быстрый (бесплатно)
   AI_PROVIDER=groq
   GROQ_API_KEY=твой_ключ
   
   # OpenAI GPT-4o-mini - быстрый и качественный
   AI_PROVIDER=openai
   OPENAI_MODEL=gpt-4o-mini
   ```

2. **Уменьши лимиты генерации:**
   ```bash
   INFOREASONS_MAX=15  # вместо 25
   ANGLES_MAX=30       # вместо 50
   HEADLINES_MAX=40    # вместо 80
   ```

### Улучшить качество

1. **Используй более мощные модели:**
   ```bash
   AI_PROVIDER=openai
   OPENAI_MODEL=gpt-4o  # вместо gpt-4o-mini
   ```

2. **Увеличь количество новостей:**
   ```bash
   NEWS_MAX_ITEMS=150  # вместо 100
   NEWS_DAYS_BACK=14   # вместо 7
   ```

3. **Настрой temperature:**
   ```bash
   # Для более креативных заголовков
   OPENAI_TEMPERATURE=0.9  # вместо 0.7
   ```

### Сэкономить на API

1. **Используй бесплатные провайдеры:**
   - **Gemini** - 1500 запросов/день бесплатно
   - **Groq** - бесплатно, быстро
   - **OpenRouter** - есть бесплатные модели

2. **Уменьши частоту автогенерации:**
   ```bash
   # Раз в неделю вместо каждые 3 дня
   SCHEDULE_CRON=0 9 * * 1
   ```

---

## 📚 Дополнительные ресурсы

### Документация используемых библиотек
- [Aiogram 3.x](https://docs.aiogram.dev/) - Telegram Bot framework
- [Google Sheets API](https://developers.google.com/sheets/api) - работа с таблицами
- [Google Drive API](https://developers.google.com/drive/api) - управление файлами
- [APScheduler](https://apscheduler.readthedocs.io/) - планировщик задач
- [Loguru](https://loguru.readthedocs.io/) - логирование
- [Pydantic](https://docs.pydantic.dev/) - валидация данных

### API провайдеры
- [OpenAI Platform](https://platform.openai.com/docs) - GPT-4o, GPT-4o-mini
- [Google AI Studio](https://ai.google.dev/docs) - Gemini 2.0
- [Anthropic Console](https://docs.anthropic.com/) - Claude 3.5
- [Groq Documentation](https://console.groq.com/docs) - Llama 3.3
- [DeepSeek Platform](https://platform.deepseek.com/docs) - DeepSeek Chat
- [OpenRouter Docs](https://openrouter.ai/docs) - агрегатор моделей

### Полезные инструменты
- [Crontab Guru](https://crontab.guru/) - генератор cron расписаний
- [BotFather](https://t.me/botfather) - создание Telegram ботов
- [userinfobot](https://t.me/userinfobot) - получить свой Telegram ID

---

## 🔐 Безопасность

### Что НЕ коммитить в Git

```bash
# Добавь в .gitignore (уже добавлено):
.env
credentials/*.json
token.json
logs/
*.log
__pycache__/
.venv/
venv/
```

### Защита API ключей

1. **Никогда не публикуй `.env` файл**
2. **Не коммить `credentials/` папку**
3. **Используй переменные окружения на сервере**
4. **Регулярно ротируй API ключи**
5. **Ограничь доступ к боту через `ADMIN_USER_IDS`**

### Ограничение доступа к боту

Только пользователи из `ADMIN_USER_IDS` могут использовать бота:

```bash
# Один админ
ADMIN_USER_IDS=123456789

# Несколько админов (через запятую)
ADMIN_USER_IDS=123456789,987654321,555555555
```

---

## 📄 Лицензия

MIT License - используй свободно для коммерческих и некоммерческих проектов.

---

## 👨‍💻 Автор и поддержка

**Версия:** 2.0  
**Последнее обновление:** 2026-05-29

**Если возникли проблемы:**
1. Проверь раздел "Решение проблем" выше
2. Посмотри логи в папке `logs/`
3. Убедись что все API ключи актуальны
4. Попробуй переустановить зависимости: `pip install -r requirements.txt --upgrade`

**Для разработчиков:**
- Код написан на Python 3.11+ с использованием async/await
- Типизация через Pydantic и type hints
- Логирование через Loguru с ротацией файлов
- Архитектура: слоистая (bot → core → database → utils)

---

**Удачи в генерации маркетинговых отчетов! 🚀**
