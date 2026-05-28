"""Обработчики команд Telegram бота."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Chat
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
    geos = list_supported_geos()
    geos_text = "\n".join(f"{flag} {name} ({code})"
                          for code, flag_name in geos
                          for flag in [flag_name.split()[0]])

    geos_str = "\n".join(f"{name}" for _, name in geos)

    await message.answer(
        f"🌍 **Поддерживаемые страны:**\n\n{geos_str}",
        reply_markup=geos_keyboard()
    )


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
    await query.message.delete()
    await _start_generation(query.message, state, geo)


@router.callback_query(F.data.startswith("confirm_generate_"))
async def cb_confirm_generate(query: CallbackQuery, state: FSMContext):
    """Подтверждение генерации."""
    geo = query.data.replace("confirm_generate_", "")
    await query.message.delete()

    # Запускаем генерацию в фоне
    await _stream_generation(query.message, state, geo)
    await query.answer()


@router.callback_query(F.data == "cancel_generate")
async def cb_cancel_generate(query: CallbackQuery, state: FSMContext):
    """Отмена генерации."""
    await query.message.delete()
    await query.message.answer("❌ Отменено")
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
    geos = list_supported_geos()
    geos_str = "\n".join(f"{name}" for _, name in geos)

    await query.answer(geos_str, show_alert=True)


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
    user_id = message.from_user.id

    try:
        generator = ReportGenerator()

        # Отслеживаем прогресс
        progress_message = None
        active_generations[user_id] = {
            "geo": geo,
            "stage": "starting",
            "progress": 0
        }

        async for status in generator.generate_report(geo):
            if status["status"] == "error":
                await message.answer(
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
                progress_message = await message.answer(status["message"])
            else:
                try:
                    await progress_message.edit_text(status["message"])
                except Exception:
                    # Игнорируем ошибки при редактировании (нет изменений)
                    pass

            if status["status"] == "completed":
                # Удаляем сообщение о прогрессе
                try:
                    await progress_message.delete()
                except Exception:
                    pass

                # Отправляем финальное сообщение с кнопкой
                sheet_url = status.get("data", {}).get("sheet_url")
                if sheet_url:
                    await message.answer(
                        "✅ Отчет готов!",
                        reply_markup=view_sheet_keyboard(sheet_url)
                    )

                # Логируем успешную генерацию
                data = status.get("data", {})
                bot_logger.info(
                    f"Отчет успешно создан для {geo}: "
                    f"{data.get('inforeasons_count', 0)} инфоповодов, "
                    f"{data.get('angles_count', 0)} углов, "
                    f"{data.get('headlines_count', 0)} заголовков"
                )

                break

    except Exception as e:
        bot_logger.exception(f"Критическая ошибка при генерации отчета: {e}")
        await message.answer(
            f"❌ Критическая ошибка: {str(e)[:100]}",
            reply_markup=main_menu_keyboard()
        )

    finally:
        # Убираем из активных генераций
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
