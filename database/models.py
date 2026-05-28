from dataclasses import dataclass, field
from datetime import datetime


# Примеры значений для AI (не ограничения, а подсказки в промптах)
# AI может генерировать любые другие значения, которые посчитает нужными

# Примеры категорий: экономика, политика, соцсети, селеба, скандал, банки-налоги, страхи
# Примеры триггеров: деньги, кризис, возможность, страх, доверие
# Примеры срочности: срочно 24-48ч, неделя, более
# Примеры типов креатива: новостной, эмоциональный, разоблачение, личная история
# Примеры приоритетов: A, B, C
# Примеры форматов заголовков: вопрос, шок, цифра, цитата, интрига
# Примеры типов источников: топовое СМИ, локальный таблоид, Twitter-тренд, TikTok, Telegram-канал, форум


@dataclass
class RawNews:
    """Сырая новость после парсинга (до обработки AI)"""
    title: str
    url: str
    date: str
    snippet: str
    source: str
    source_type: str | None = None


@dataclass
class InfoReason:
    """Блок 1: Сырой инфоповод (обработанный AI)"""
    id: int
    title: str  # заголовок инфоповода
    source_url: str  # источник со ссылкой
    source_type: str  # тип источника (AI определяет сам)
    date: str  # дата
    category: str  # категория (AI определяет сам)
    description: str  # краткое описание в 2-3 предложения
    emotional_trigger: str  # эмоциональный триггер (AI определяет сам)
    urgency: str  # срок актуальности (AI определяет сам)


@dataclass
class Angle:
    """Блок 2: Угол и идея (связка инфоповод → угол → оффер)"""
    id: int  # номер идеи
    inforeason_id: int  # к какому инфоповоду привязана
    angle_text: str  # формулировка угла
    offer_connection: str  # как связывается с оффером
    target_pain: str  # целевая боль аудитории
    creative_type: str  # тип креатива (AI определяет сам)
    priority: str  # приоритет тестирования (AI определяет сам, обычно A/B/C)


@dataclass
class Headline:
    """Блок 3: Заголовок (сгруппированы по идеям)"""
    id: int
    angle_id: int  # идея-родитель
    text: str  # текст заголовка
    format: str  # формат (AI определяет сам)
    length: int = 0  # длина в символах

    def __post_init__(self):
        """Автоматически вычисляем длину если не указана"""
        if self.length == 0:
            self.length = len(self.text)


@dataclass
class Recommendation:
    """Блок 4: Рекомендация к тесту (топ-5 идей)"""
    rank: int  # ранг (1-5)
    angle_id: int  # ID идеи
    reasoning: str  # обоснование — почему именно эта идея
    freshness_score: int  # свежесть инфоповода (1-10)
    trigger_strength_score: int  # сила триггера (1-10)
    offer_fit_score: int  # соответствие офферу (1-10)
    # топ-3 заголовка для этой идеи
    top_headlines: list[int] = field(default_factory=list)


@dataclass
class Risk:
    """Блок 5: Риски (по каждому инфоповоду из топа)"""
    inforeason_id: int
    legal_risk: str  # юридические риски
    platform_ban_risk: str  # риск бана платформой
    audience_backlash_risk: str  # риск негатива аудитории
    reputation_risk: str  # репутационный риск
    expiry_time: str  # срок «протухания»


@dataclass
class UrgencyBoard:
    """Блок 6: Срочность — сводный список"""
    urgent_48h: list[int] = field(
        default_factory=list)  # 🔥 Срочно (ID инфоповодов)
    # ⏳ Можно позже (ID инфоповодов)
    can_wait: list[int] = field(default_factory=list)


@dataclass
class Feedback:
    """Блок обратной связи по прошлым выпускам"""
    previous_report_url: str | None = None  # ссылка на предыдущий выпуск
    successful_inforeasons: list[str] = field(
        default_factory=list)  # какие инфоповоды конвертили
    failed_inforeasons: list[str] = field(
        default_factory=list)  # какие не зашли
    notes: str = ""  # дополнительные заметки


@dataclass
class Report:
    """Полный отчет (контейнер для всех блоков)"""
    # Шапка
    geo: str  # Страна/GEO
    date: str  # дата генерации
    period_start: str  # начало периода покрытия новостей
    period_end: str  # конец периода покрытия новостей
    responsible: str | None = None  # ответственный тимлид

    # Блоки данных
    inforeasons: list[InfoReason] = field(default_factory=list)  # Блок 1
    angles: list[Angle] = field(default_factory=list)  # Блок 2
    headlines: list[Headline] = field(default_factory=list)  # Блок 3
    recommendations: list[Recommendation] = field(
        default_factory=list)  # Блок 4
    risks: list[Risk] = field(default_factory=list)  # Блок 5
    urgency_board: UrgencyBoard | None = None  # Блок 6
    feedback: Feedback | None = None  # Блок обратной связи

    # Метаданные
    # ссылка на Google Sheets (заполняется после создания)
    sheet_url: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_urgent_inforeasons(self) -> list[InfoReason]:
        """Получить срочные инфоповоды (24-48ч)"""
        return [ir for ir in self.inforeasons if "срочно" in ir.urgency.lower() or "24" in ir.urgency]

    def get_angles_by_priority(self, priority: str) -> list[Angle]:
        """Получить углы по приоритету (например A/B/C)"""
        return [angle for angle in self.angles if angle.priority == priority]

    def get_headlines_for_angle(self, angle_id: int) -> list[Headline]:
        """Получить все заголовки для конкретного угла"""
        return [h for h in self.headlines if h.angle_id == angle_id]

    def get_inforeason_by_id(self, inforeason_id: int) -> InfoReason | None:
        """Получить инфоповод по ID"""
        for ir in self.inforeasons:
            if ir.id == inforeason_id:
                return ir
        return None

    def get_angle_by_id(self, angle_id: int) -> Angle | None:
        """Получить угол по ID"""
        for angle in self.angles:
            if angle.id == angle_id:
                return angle
        return None
