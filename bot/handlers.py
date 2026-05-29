"""Обработчики команд Telegram бота."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards import (
    main_menu_keyboard, geos_keyboard, confirm_generate_keyboard,
    view_sheet_keyboard
)
from config import settings
from core.report_generator import ReportGenerator
from core.scheduler import get_scheduler
from utils.helpers import format_geo_title, list_supported_geos, GeoError
from utils.logger import bot_logger


router = Router()

# FSM для отслеживания состояния


class GenerationStates(StatesGroup):
    waiting_for_geo = State()
    generating = State()


# Хранилище активных генераций (простая реализация)
active_generations: dict[int, dict] = {}


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start - приветствие и меню."""
    await message.answer(
        "👋 Добро пожаловать в AI Monitor Bot!\n\n"
        "Я помогу вам генерировать отчеты по инфоповодам и маркетинговым идеям.\n\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help - справка по командам."""
    geos = list_supported_geos()
    geos_str = ", ".join(code for code, _ in geos)

    help_text = f"""📋 **Доступные команды:**

/start - Главное меню
/help - Справка (эта справка)
/generate [GEO] - Генерировать отчет для страны
/status - Статус активных генераций
/geos - Список поддерживаемых стран
/cancel - Отменить текущую генерацию

🌍 **Поддерживаемые страны (GEO):**
{geos_str}

Пример: `/generate BR` - генерировать отчет для Бразилии

❓ **Вопросы?** Обратитесь к администратору."""

    await message.answer(help_text)


@router.message(Command("geos"))
async def cmd_geos(message: Message):
    """Команда /geos - список поддерживаемых GEO."""
    from utils.helpers import GEO_REGISTRY

    # Разбиваем на регионы для компактности
    latam_codes = ["AR", "BO", "BR", "CL", "CO", "CR", "DO", "EC",
                   "GT", "HN", "MX", "NI", "PA", "PE", "PY", "SV", "UY", "VE"]
    asia_codes = ["IN", "ID", "PH", "TH", "VN"]
    africa_codes = ["NG", "ZA", "KE"]

    text = "🌍 **Поддерживаемые страны:**\n\n"

    text += "🌎 **Латинская Америка:**\n"
    text += ", ".join(
        f"{GEO_REGISTRY[code]['flag']}{code}" for code in latam_codes)

    text += "\n\n🌏 **Азия:**\n"
    text += ", ".join(
        f"{GEO_REGISTRY[code]['flag']}{code}" for code in asia_codes)

    text += "\n\n🌍 **Африка:**\n"
    text += ", ".join(
        f"{GEO_REGISTRY[code]['flag']}{code}" for code in africa_codes)

    await message.answer(text, reply_markup=geos_keyboard())


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Команда /status - статус активных генераций."""
    user_id = message.from_user.id

    if user_id in active_generations:
        gen_data = active_generations[user_id]
        status_text = f"⏳ **Генерация для {gen_data['geo']}**\n\n"
        status_text += f"Статус: {gen_data.get('stage', '?')}\n"
        status_text += f"Прогресс: {gen_data.get('progress', 0)}%"
    else:
        status_text = "✅ Нет активных генераций"

    scheduler = get_scheduler()
    next_runs = scheduler.get_next_runs()

    if next_runs:
        status_text += "\n\n📅 **Планируемые запуски:**\n"
        for run in next_runs[:3]:
            status_text += f"- {run['next_run']}\n"

    await message.answer(status_text)


@router.message(Command("generate"))
async def cmd_generate(message: Message, state: FSMContext):
    """Команда /generate [GEO] - генерация отчета."""
    parts = message.text.split()

    if len(parts) < 2:
        # Просим выбрать GEO
        await message.answer(
            "Выберите страну для генерации отчета:",
            reply_markup=geos_keyboard()
        )
        await state.set_state(GenerationStates.waiting_for_geo)
    else:
        # GEO указана в команде
        geo = parts[1].upper()
        await _start_generation(message, state, geo)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Команда /cancel - отмена генерации."""
    user_id = message.from_user.id

    if user_id in active_generations:
        del active_generations[user_id]
        await message.answer("❌ Генерация отменена")
    else:
        await message.answer("✅ Нет активных генераций")

    await state.clear()


# Callback обработчики для меню
@router.callback_query(F.data == "generate_menu")
async def cb_generate_menu(query: CallbackQuery, state: FSMContext):
    """Кнопка 'Генерировать отчет'."""
    await query.message.edit_text(
        "Выберите страну:",
        reply_markup=geos_keyboard()
    )
    await state.set_state(GenerationStates.waiting_for_geo)
    await query.answer()


@router.callback_query(F.data.startswith("geo_"))
async def cb_select_geo(query: CallbackQuery, state: FSMContext):
    """Выбор GEO из клавиатуры."""
    geo = query.data.replace("geo_", "")

    try:
        geo = geo.upper()
        geo_title = format_geo_title(geo)

        await query.message.edit_text(
            f"Подтвердите генерацию отчета для {geo_title}?",
            reply_markup=confirm_generate_keyboard(geo)
        )

        await state.update_data(selected_geo=geo)
        await query.answer()

    except GeoError as e:
        await query.message.edit_text(f"❌ Ошибка: {str(e)}")
        await query.answer()


@router.callback_query(F.data.startswith("confirm_generate_"))
async def cb_confirm_generate(query: CallbackQuery, state: FSMContext):
    """Подтверждение генерации."""
    geo = query.data.replace("confirm_generate_", "")

    await query.message.edit_text("⏳ Начинаю генерацию...")
    await query.answer()

    # Запускаем генерацию
    await _stream_generation(query.message, state, geo)


@router.callback_query(F.data == "cancel_generate")
async def cb_cancel_generate(query: CallbackQuery, state: FSMContext):
    """Отмена генерации."""
    await query.message.edit_text("❌ Отменено")
    await state.clear()
    await query.answer()


@router.callback_query(F.data == "status")
async def cb_status(query: CallbackQuery):
    """Кнопка 'Статус'."""
    user_id = query.from_user.id

    if user_id in active_generations:
        gen_data = active_generations[user_id]
        status_text = f"⏳ Генерация для {gen_data['geo']}\n"
        status_text += f"Прогресс: {gen_data.get('progress', 0)}%"
    else:
        status_text = "✅ Нет активных генераций"

    await query.answer(status_text, show_alert=True)


@router.callback_query(F.data == "list_geos")
async def cb_list_geos(query: CallbackQuery):
    """Кнопка 'Доступные GEO'."""
    from utils.helpers import GEO_REGISTRY

    latam_codes = ["AR", "BO", "BR", "CL", "CO", "CR", "DO", "EC",
                   "GT", "HN", "MX", "NI", "PA", "PE", "PY", "SV", "UY", "VE"]
    asia_codes = ["IN", "ID", "PH", "TH", "VN"]
    africa_codes = ["NG", "ZA", "KE"]

    text = "🌍 **Поддерживаемые страны:**\n\n"
    text += "🌎 **Латинская Америка:**\n"
    text += ", ".join(
        f"{GEO_REGISTRY[code]['flag']}{code}" for code in latam_codes)
    text += "\n\n🌏 **Азия:**\n"
    text += ", ".join(
        f"{GEO_REGISTRY[code]['flag']}{code}" for code in asia_codes)
    text += "\n\n🌍 **Африка:**\n"
    text += ", ".join(
        f"{GEO_REGISTRY[code]['flag']}{code}" for code in africa_codes)

    # Отправляем как новое сообщение, а не через callback answer (лимит 200 символов)
    await query.message.answer(text, reply_markup=geos_keyboard())
    await query.answer()  # Просто закрываем callback без текста


async def _start_generation(message: Message, state: FSMContext, geo: str):
    """Запуск генерации после выбора GEO."""
    try:
        geo = geo.upper()
        geo_title = format_geo_title(geo)

        await message.answer(
            f"Подтвердите генерацию отчета для {geo_title}?",
            reply_markup=confirm_generate_keyboard(geo)
        )

        await state.update_data(selected_geo=geo)

    except GeoError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


async def _stream_generation(message: Message, state: FSMContext, geo: str):
    """Генерация отчета с потоком статусов."""
    bot = message.bot
    user_id = message.chat.id

    try:
        generator = ReportGenerator()
        progress_message = None
        active_generations[user_id] = {
            "geo": geo,
            "stage": "starting",
            "progress": 0
        }

        async for status in generator.generate_report(geo):
            if status["status"] == "error":
                await bot.send_message(
                    message.chat.id,
                    status["message"],
                    reply_markup=main_menu_keyboard()
                )
                bot_logger.error(
                    f"Ошибка генерации: {status.get('data', {}).get('error')}")
                break

            # Обновляем данные активной генерации
            active_generations[user_id].update({
                "stage": status["stage"],
                "progress": status["progress"]
            })

            # Отправляем или обновляем сообщение о прогрессе
            if progress_message is None:
                progress_message = await bot.send_message(message.chat.id, status["message"])
            else:
                try:
                    await bot.edit_message_text(
                        status["message"],
                        message.chat.id,
                        progress_message.message_id
                    )
                except Exception:
                    pass

            if status["status"] == "completed" and status["stage"] == "sheets":
                try:
                    await bot.delete_message(message.chat.id, progress_message.message_id)
                except Exception:
                    pass

                sheet_url = status.get("data", {}).get("sheet_url")
                data = status.get("data", {})

                if sheet_url:
                    await bot.send_message(
                        message.chat.id,
                        "✅ Отчет готов!",
                        reply_markup=view_sheet_keyboard(sheet_url)
                    )
                else:
                    # Если Google Sheets недоступен, отправляем только статистику
                    await bot.send_message(
                        message.chat.id,
                        f"✅ Отчет создан!\n\n"
                        f"📊 Статистика:\n"
                        f"• Инфоповодов: {data.get('inforeasons_count', 0)}\n"
                        f"• Углов: {data.get('angles_count', 0)}\n"
                        f"• Заголовков: {data.get('headlines_count', 0)}\n\n"
                        f"⚠️ Google Sheets недоступен, отчет сохранен локально.",
                        reply_markup=main_menu_keyboard()
                    )

                bot_logger.info(
                    f"Отчет успешно создан для {geo}: "
                    f"{data.get('inforeasons_count', 0)} инфоповодов, "
                    f"{data.get('angles_count', 0)} углов, "
                    f"{data.get('headlines_count', 0)} заголовков"
                )
                break

    except Exception as e:
        bot_logger.exception(f"Критическая ошибка при генерации отчета: {e}")
        await bot.send_message(
            message.chat.id,
            f"❌ Критическая ошибка: {str(e)[:100]}",
            reply_markup=main_menu_keyboard()
        )

    finally:
        if user_id in active_generations:
            del active_generations[user_id]
        await state.clear()


async def scheduled_generate_all_geos():
    """Планировщик: автоматическая генерация для всех приоритетных GEO."""
    # Генерируем для приоритетных GEO (по умолчанию: BR, MX, AR)
    priority_geos = ['BR', 'MX', 'AR']

    bot_logger.info(f"Начало плановой генерации для GEO: {priority_geos}")

    generator = ReportGenerator()

    for geo in priority_geos:
        try:
            bot_logger.info(f"Плановая генерация для {geo}...")

            # Просто генерируем и игнорируем результаты (они уже в Google Sheets)
            async for status in generator.generate_report(geo):
                if status["status"] == "completed":
                    bot_logger.info(f"✅ Плановый отчет для {geo} готов")
                    break
                elif status["status"] == "error":
                    bot_logger.error(
                        f"❌ Ошибка плановой генерации для {geo}: {status.get('message')}")
                    break

        except Exception as e:
            bot_logger.exception(
                f"Ошибка при плановой генерации для {geo}: {e}")

    bot_logger.info("Плановая генерация завершена")
