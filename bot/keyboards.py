"""Telegram inline клавиатуры и кнопки."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.helpers import list_supported_geos


def geos_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора GEO."""
    buttons = []
    geos = list_supported_geos()

    for code, display_name in geos:
        buttons.append(
            [InlineKeyboardButton(
                text=display_name,
                callback_data=f"geo_{code}"
            )]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_generate_keyboard(geo_code: str) -> InlineKeyboardMarkup:
    """Подтверждение генерации отчета для GEO."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, генерировать",
                                 callback_data=f"confirm_generate_{geo_code}"),
            InlineKeyboardButton(
                text="❌ Отмена", callback_data="cancel_generate"),
        ]
    ])


def view_sheet_keyboard(sheet_url: str) -> InlineKeyboardMarkup:
    """Кнопка для открытия Google Sheets."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📊 Открыть в Google Sheets", url=sheet_url)],
        [InlineKeyboardButton(text="🔄 Переоформить",
                              callback_data="regenerate")],
    ])


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Генерировать отчет",
                              callback_data="generate_menu")],
        [InlineKeyboardButton(text="📊 Статус", callback_data="status")],
        [InlineKeyboardButton(text="🌍 Доступные GEO",
                              callback_data="list_geos")],
    ])
