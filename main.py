"""Главная точка входа бота."""

import asyncio
import sys
from signal import SIGINT, SIGTERM

from aiogram import Dispatcher, Bot
from aiogram.types import BotCommand

from bot.handlers import router
from bot.middlewares import LoggingMiddleware, ErrorHandlerMiddleware
from config import settings
from core.scheduler import get_scheduler
from utils.logger import setup_logging, bot_logger


async def setup_bot_commands(bot: Bot):
    """Регистрация команд в меню Telegram."""
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="Справка"),
        BotCommand(command="generate", description="Генерировать отчет"),
        BotCommand(command="status", description="Статус генерации"),
        BotCommand(command="geos", description="Поддерживаемые страны"),
        BotCommand(command="cancel", description="Отмена генерации"),
    ]
    await bot.set_my_commands(commands)
    bot_logger.info("Команды бота регистрации успешно")


async def main():
    """Главная функция."""
    # Настройка логирования
    setup_logging()

    bot_logger.info(f"🚀 Запуск бота (режим: {settings.MODE})")
    bot_logger.info(f"AI провайдер: {settings.AI_PROVIDER}")

    # Инициализация бота
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация маршрутов и middlewares
    dp.include_router(router)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())

    # Регистрация команд
    await setup_bot_commands(bot)

    # Запуск планировщика (если не TEST режим)
    scheduler = get_scheduler()
    if settings.MODE != 'TEST':
        scheduler.start()
        bot_logger.info("📅 Планировщик запущен")

    try:
        # Graceful shutdown обработчик
        loop = asyncio.get_event_loop()

        for sig in (SIGINT, SIGTERM):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda: asyncio.create_task(_shutdown(bot, dp, scheduler))
                )
            except NotImplementedError:
                bot_logger.warning(
                    "loop.add_signal_handler not supported on this platform; graceful shutdown disabled")

        bot_logger.info("✅ Бот готов к работе")
        await dp.start_polling(bot)

    finally:
        await bot.session.close()


async def _shutdown(bot: Bot, dp: Dispatcher, scheduler):
    """Graceful shutdown."""
    bot_logger.info("🛑 Получен сигнал завершения...")

    scheduler.stop()

    await dp.feed_update(None)  # Signal to stop polling
    await bot.session.close()

    bot_logger.info("✅ Бот успешно остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.info("Бот остановлен пользователем")
        sys.exit(0)
    except Exception as e:
        bot_logger.exception(f"Критическая ошибка бота: {e}")
        sys.exit(1)
