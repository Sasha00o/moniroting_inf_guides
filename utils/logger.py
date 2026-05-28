import sys
from pathlib import Path
from loguru import logger
from config import settings

LOGS_DIR = Path("logs")

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)
_ERROR_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}"
)
_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


class _ComponentLogger:
    """Прокси: импорт до setup_logging() остаётся рабочим после инициализации handlers."""

    __slots__ = ("_component",)

    def __init__(self, component: str) -> None:
        self._component = component

    def __getattr__(self, name: str):
        return getattr(logger.bind(component=self._component), name)


bot_logger = _ComponentLogger("bot")
ai_logger = _ComponentLogger("ai")
sheets_logger = _ComponentLogger("sheets")
news_logger = _ComponentLogger("news")
generator_logger = _ComponentLogger("generator")
scheduler_logger = _ComponentLogger("scheduler")


def setup_exception_logging():
    """Настроить отлов необработанных исключений."""

    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            "Необработанное исключение"
        )

    sys.excepthook = exception_handler


def setup_json_logging():
    """Настроить JSON логирование для продакшена."""
    logger.add(
        LOGS_DIR / "app.json",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        level="INFO",
        serialize=True,
        enqueue=True,
    )


def _component_filter(component: str):
    return lambda record: record["extra"].get("component") == component


def setup_logging():
    """Инициализировать всю систему логирования."""
    LOGS_DIR.mkdir(exist_ok=True)
    logger.remove()

    logger.add(
        sys.stdout,
        format=_CONSOLE_FORMAT,
        level=settings.LOG_LEVEL,
        colorize=True,
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "app.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="INFO",
        format=_FILE_FORMAT,
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "errors.log",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        level="ERROR",
        format=_ERROR_FORMAT,
        enqueue=True,
    )

    setup_exception_logging()

    if settings.MODE == "PROD":
        setup_json_logging()

    logger.add(
        LOGS_DIR / "bot.log",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format=_FILE_FORMAT,
        filter=_component_filter("bot"),
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "ai.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format=_FILE_FORMAT,
        filter=_component_filter("ai"),
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "sheets.log",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format=_FILE_FORMAT,
        filter=_component_filter("sheets"),
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "news.log",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format=_FILE_FORMAT,
        filter=_component_filter("news"),
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "generator.log",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format=_FILE_FORMAT,
        filter=_component_filter("generator"),
        enqueue=True,
    )

    logger.add(
        LOGS_DIR / "scheduler.log",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG",
        format=_FILE_FORMAT,
        filter=_component_filter("scheduler"),
        enqueue=True,
    )

    logger.info("Система логирования инициализирована")
    logger.info(f"Режим: {settings.MODE}, Уровень: {settings.LOG_LEVEL}")
