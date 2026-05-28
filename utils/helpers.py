"""Вспомогательные функции: GEO, даты, retry."""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Awaitable, Callable
from datetime import date, datetime, timedelta
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class GeoError(ValueError):
    """Невалидный или неподдерживаемый код GEO."""


# gl/hl — параметры Google News RSS; locale — для отображения в отчёте
GEO_REGISTRY: dict[str, dict[str, str]] = {
    "AR": {"name": "Аргентина", "flag": "🇦🇷", "gl": "AR", "hl": "es-419", "locale": "es_AR"},
    "BO": {"name": "Боливия", "flag": "🇧🇴", "gl": "BO", "hl": "es-419", "locale": "es_BO"},
    "BR": {"name": "Бразилия", "flag": "🇧🇷", "gl": "BR", "hl": "pt-BR", "locale": "pt_BR"},
    "CL": {"name": "Чили", "flag": "🇨🇱", "gl": "CL", "hl": "es-419", "locale": "es_CL"},
    "CO": {"name": "Колумбия", "flag": "🇨🇴", "gl": "CO", "hl": "es-419", "locale": "es_CO"},
    "CR": {"name": "Коста-Рика", "flag": "🇨🇷", "gl": "CR", "hl": "es-419", "locale": "es_CR"},
    "DO": {"name": "Доминикана", "flag": "🇩🇴", "gl": "DO", "hl": "es-419", "locale": "es_DO"},
    "EC": {"name": "Эквадор", "flag": "🇪🇨", "gl": "EC", "hl": "es-419", "locale": "es_EC"},
    "GT": {"name": "Гватемала", "flag": "🇬🇹", "gl": "GT", "hl": "es-419", "locale": "es_GT"},
    "HN": {"name": "Гондурас", "flag": "🇭🇳", "gl": "HN", "hl": "es-419", "locale": "es_HN"},
    "MX": {"name": "Мексика", "flag": "🇲🇽", "gl": "MX", "hl": "es-419", "locale": "es_MX"},
    "NI": {"name": "Никарагуа", "flag": "🇳🇮", "gl": "NI", "hl": "es-419", "locale": "es_NI"},
    "PA": {"name": "Панама", "flag": "🇵🇦", "gl": "PA", "hl": "es-419", "locale": "es_PA"},
    "PE": {"name": "Перу", "flag": "🇵🇪", "gl": "PE", "hl": "es-419", "locale": "es_PE"},
    "PY": {"name": "Парагвай", "flag": "🇵🇾", "gl": "PY", "hl": "es-419", "locale": "es_PY"},
    "SV": {"name": "Сальвадор", "flag": "🇸🇻", "gl": "SV", "hl": "es-419", "locale": "es_SV"},
    "UY": {"name": "Уругвай", "flag": "🇺🇾", "gl": "UY", "hl": "es-419", "locale": "es_UY"},
    "VE": {"name": "Венесуэла", "flag": "🇻🇪", "gl": "VE", "hl": "es-419", "locale": "es_VE"},
    "IN": {"name": "Индия", "flag": "🇮🇳", "gl": "IN", "hl": "en-IN", "locale": "en_IN"},
    "ID": {"name": "Индонезия", "flag": "🇮🇩", "gl": "ID", "hl": "id", "locale": "id_ID"},
    "PH": {"name": "Филиппины", "flag": "🇵🇭", "gl": "PH", "hl": "en-PH", "locale": "en_PH"},
    "TH": {"name": "Таиланд", "flag": "🇹🇭", "gl": "TH", "hl": "th", "locale": "th_TH"},
    "VN": {"name": "Вьетнам", "flag": "🇻🇳", "gl": "VN", "hl": "vi", "locale": "vi_VN"},
    "NG": {"name": "Нигерия", "flag": "🇳🇬", "gl": "NG", "hl": "en-NG", "locale": "en_NG"},
    "ZA": {"name": "ЮАР", "flag": "🇿🇦", "gl": "ZA", "hl": "en-ZA", "locale": "en_ZA"},
    "KE": {"name": "Кения", "flag": "🇰🇪", "gl": "KE", "hl": "en-KE", "locale": "en_KE"},
}


def normalize_geo(geo: str) -> str:
    """Привести код GEO к верхнему регистру."""
    return geo.strip().upper()


def validate_geo(geo: str) -> str:
    """
    Проверить код GEO и вернуть нормализованный код.

    Raises:
        GeoError: если GEO не в списке поддерживаемых.
    """
    code = normalize_geo(geo)
    if code not in GEO_REGISTRY:
        supported = ", ".join(sorted(GEO_REGISTRY))
        raise GeoError(
            f"GEO '{geo}' не поддерживается. Доступные коды: {supported}"
        )
    return code


def get_geo_info(geo: str) -> dict[str, str]:
    """Метаданные GEO после валидации."""
    return GEO_REGISTRY[validate_geo(geo)]


def format_geo_title(geo: str) -> str:
    """Заголовок для шапки отчёта, например «🇧🇷 БРАЗИЛИЯ»."""
    info = get_geo_info(geo)
    return f"{info['flag']} {info['name'].upper()}"


def list_supported_geos() -> list[tuple[str, str]]:
    """Список (код, отображаемое имя) для команд бота."""
    return [
        (code, f"{meta['flag']} {meta['name']} ({code})")
        for code, meta in sorted(GEO_REGISTRY.items())
    ]


def today() -> date:
    return date.today()


def format_date(d: date | datetime | None = None, fmt: str = "%Y-%m-%d") -> str:
    """Дата в строку (по умолчанию ISO для имён файлов)."""
    if d is None:
        d = today()
    elif isinstance(d, datetime):
        d = d.date()
    return d.strftime(fmt)


def format_date_display(d: date | datetime | None = None) -> str:
    """Дата для отображения в таблице: 28.05.26."""
    if d is None:
        d = today()
    elif isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d.%m.%y")


def news_period(days_back: int = 7, end: date | None = None) -> tuple[date, date]:
    """
    Период покрытия новостей.

    Returns:
        (period_start, period_end) — включительно.
    """
    period_end = end or today()
    period_start = period_end - timedelta(days=days_back)
    return period_start, period_end


def format_period_display(
    period_start: date, period_end: date
) -> str:
    """Период для шапки отчёта, например «21–28 мая 2026»."""
    months_ru = (
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )
    if period_start.year == period_end.year and period_start.month == period_end.month:
        month = months_ru[period_end.month - 1]
        return f"{period_start.day}–{period_end.day} {month} {period_end.year}"
    return f"{format_date_display(period_start)} – {format_date_display(period_end)}"


def report_filename(geo: str, on_date: date | None = None) -> str:
    """Имя файла Google Sheets: BR_2026-05-28."""
    code = validate_geo(geo)
    return f"{code}_{format_date(on_date)}"


def retry(
    *,
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Декоратор retry с экспоненциальной задержкой (синхронные функции)."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            wait = delay
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == attempts:
                        break
                    time.sleep(wait)
                    wait *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


def async_retry(
    *,
    attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Декоратор retry с экспоненциальной задержкой (async функции)."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            wait = delay
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == attempts:
                        break
                    await asyncio.sleep(wait)
                    wait *= backoff
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator
