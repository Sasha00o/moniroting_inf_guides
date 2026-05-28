"""Middlewares для логирования и обработки ошибок."""

from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from utils.logger import bot_logger


class LoggingMiddleware(BaseMiddleware):
    """Логирование всех событий."""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Any],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        if event.message:
            user_id = event.message.from_user.id
            text = event.message.text or "[не текст]"
            bot_logger.debug(f"Message from {user_id}: {text[:100]}")
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            data_str = event.callback_query.data or "[empty]"
            bot_logger.debug(f"Callback from {user_id}: {data_str}")

        try:
            return await handler(event, data)
        except Exception as e:
            bot_logger.exception(f"Ошибка обработки события: {e}")
            raise


class ErrorHandlerMiddleware(BaseMiddleware):
    """Обработка ошибок и graceful degradation."""

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Any],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except ValueError as e:
            # Ошибки валидации — показываем пользователю
            bot_logger.warning(f"Validation error: {e}")
            if event.message:
                await event.message.answer(
                    f"❌ Ошибка: {str(e)[:200]}"
                )
        except Exception as e:
            # Неожиданные ошибки — логируем и показываем generic message
            bot_logger.exception(f"Unexpected error: {e}")
            if event.message:
                await event.message.answer(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
                )
            elif event.callback_query:
                try:
                    await event.callback_query.answer(
                        "❌ Ошибка обработки",
                        show_alert=True
                    )
                except Exception:
                    pass
            raise
