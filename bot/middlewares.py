"""Middlewares для логирования и обработки ошибок."""

from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

from utils.logger import bot_logger


class LoggingMiddleware(BaseMiddleware):
    """Логирование всех событий."""

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Any],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id
            text = event.text or "[не текст]"
            bot_logger.debug(f"Message from {user_id}: {text[:100]}")
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            data_str = event.data or "[empty]"
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
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Any],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except ValueError as e:
            # Ошибки валидации — показываем пользователю
            bot_logger.warning(f"Validation error: {e}")
            if isinstance(event, Message):
                await event.answer(
                    f"❌ Ошибка: {str(e)[:200]}"
                )
        except Exception as e:
            # Неожиданные ошибки — логируем и показываем generic message
            bot_logger.exception(f"Unexpected error: {e}")
            if isinstance(event, Message):
                await event.answer(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
                )
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer(
                        "❌ Ошибка обработки",
                        show_alert=True
                    )
                except Exception:
                    pass
            raise
