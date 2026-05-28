import json
from typing import List
from anthropic import Anthropic

from database.models import RawNews, InfoReason, Angle, Headline, Risk, Recommendation
from utils.logger import ai_logger
from config import settings


class AIAgent:
    """AI агент для обработки новостей и генерации маркетинговых идей."""

    def __init__(self):
        """Инициализация AI клиента на основе выбранного провайдера."""
        self.provider = settings.AI_PROVIDER
        ai_logger.info(
            f"Инициализация AI агента: провайдер={self.provider}, модель={settings.ACTIVE_AI_MODEL}")

        if self.provider == "claude":
            self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.client = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            raise ValueError(f"Неподдерживаемый AI провайдер: {self.provider}")

    async def classify_inforeasons(
        self,
        news_items: List[RawNews],
        geo: str,
        min_count: int = None,
        max_count: int = None
    ) -> List[InfoReason]:
        """
        Анализ новостей и создание инфоповодов.

        Args:
            news_items: Список сырых новостей
            geo: Код страны
            min_count: Минимальное количество инфоповодов
            max_count: Максимальное количество инфоповодов

        Returns:
            Список объектов InfoReason
        """
        if min_count is None:
            min_count = settings.INFOREASONS_MIN
        if max_count is None:
            max_count = settings.INFOREASONS_MAX

        ai_logger.info(
            f"Классификация {len(news_items)} новостей в инфоповоды для {geo}")

        # Формирование промпта
        news_text = self._format_news_for_prompt(news_items)

        prompt = f"""Ты — эксперт по маркетингу и анализу новостей для {geo}.

Твоя задача: проанализировать новости и выбрать {min_count}-{max_count} самых сильных инфоповодов для маркетинговых кампаний.

КРИТЕРИИ ОТБОРА:
1. Эмоциональный триггер (деньги, страх, возможность, кризис, доверие)
2. Актуальность и свежесть
3. Потенциал для связи с офферами (финансы, недвижимость, образование, здоровье)
4. Широкий охват аудитории

НОВОСТИ:
{news_text}

Для каждого инфоповода верни JSON объект:
{{
  "id": <номер 1, 2, 3...>,
  "title": "<заголовок инфоповода>",
  "source_url": "<URL источника>",
  "source_type": "<тип источника: топовое СМИ / локальный таблоид / соцсети / форум>",
  "date": "<дата в формате YYYY-MM-DD>",
  "category": "<категория: экономика / политика / соцсети / селеба / скандал / банки-налоги / страхи / технологии / здоровье>",
  "description": "<краткое описание в 2-3 предложения>",
  "emotional_trigger": "<эмоциональный триггер: деньги / кризис / возможность / страх / доверие / жадность / FOMO>",
  "urgency": "<срок актуальности: срочно 24-48ч / неделя / более>",
}}

Верни ТОЛЬКО валидный JSON массив объектов, без дополнительного текста:
[{{"id": 1, ...}}, {{"id": 2, ...}}]"""

        try:
            # Вызов AI
            response_text = await self._call_ai(prompt, temperature=0.3)

            # Парсинг JSON
            inforeasons_data = self._parse_json_response(response_text)

            # Создание объектов InfoReason
            inforeasons = []
            for data in inforeasons_data[:max_count]:
                inforeason = InfoReason(
                    id=data["id"],
                    title=data["title"],
                    source_url=data["source_url"],
                    source_type=data.get("source_type", "неизвестно"),
                    date=data["date"],
                    category=data["category"],
                    description=data["description"],
                    emotional_trigger=data["emotional_trigger"],
                    urgency=data["urgency"]
                )
                inforeasons.append(inforeason)

            ai_logger.info(f"Создано {len(inforeasons)} инфоповодов")
            return inforeasons

        except Exception as e:
            ai_logger.error(
                f"Ошибка классификации инфоповодов: {e}", exc_info=True)
            raise

    async def generate_angles(
        self,
        inforeasons: List[InfoReason],
        offer_description: str = None,
        min_count: int = None,
        max_count: int = None
    ) -> List[Angle]:
        """
        Генерация маркетинговых углов на основе инфоповодов.

        Args:
            inforeasons: Список инфоповодов
            offer_description: Описание оффера (опционально)
            min_count: Минимальное количество углов
            max_count: Максимальное количество углов

        Returns:
            Список объектов Angle
        """
        if min_count is None:
            min_count = settings.ANGLES_MIN
        if max_count is None:
            max_count = settings.ANGLES_MAX

        ai_logger.info(f"Генерация углов для {len(inforeasons)} инфоповодов")

        # Формирование промпта
        inforeasons_text = self._format_inforeasons_for_prompt(inforeasons)
        offer_text = f"\n\nОПИСАНИЕ ОФФЕРА:\n{offer_description}" if offer_description else ""

        prompt = f"""Ты — креативный маркетолог. Твоя задача: создать {min_count}-{max_count} маркетинговых углов на основе инфоповодов.

ИНФОПОВОДЫ:
{inforeasons_text}{offer_text}

Для каждого инфоповода создай 2-3 разных угла (разные подходы к одной новости).

ТРЕБОВАНИЯ К УГЛУ:
1. Четкая связь инфоповод → угол → оффер
2. Целевая боль аудитории
3. Эмоциональный крючок
4. Конкретная формулировка (не общие слова)

Для каждого угла верни JSON объект:
{{
  "id": <номер угла 1, 2, 3...>,
  "inforeason_id": <ID инфоповода>,
  "angle_text": "<формулировка угла>",
  "offer_connection": "<как связывается с оффером>",
  "target_pain": "<целевая боль аудитории>",
  "creative_type": "<тип креатива: новостной / эмоциональный / разоблачение / личная история / сравнение>",
  "priority": "<приоритет тестирования: A / B / C>"
}}

Верни ТОЛЬКО валидный JSON массив, без дополнительного текста:
[{{"id": 1, ...}}, {{"id": 2, ...}}]"""

        try:
            response_text = await self._call_ai(prompt, temperature=0.7)
            angles_data = self._parse_json_response(response_text)

            angles = []
            for data in angles_data[:max_count]:
                angle = Angle(
                    id=data["id"],
                    inforeason_id=data["inforeason_id"],
                    angle_text=data["angle_text"],
                    offer_connection=data["offer_connection"],
                    target_pain=data["target_pain"],
                    creative_type=data["creative_type"],
                    priority=data["priority"]
                )
                angles.append(angle)

            ai_logger.info(f"Создано {len(angles)} углов")
            return angles

        except Exception as e:
            ai_logger.error(f"Ошибка генерации углов: {e}", exc_info=True)
            raise

    async def generate_headlines(
        self,
        angles: List[Angle],
        min_count: int = None,
        max_count: int = None
    ) -> List[Headline]:
        """
        Генерация заголовков для углов.

        Args:
            angles: Список углов
            min_count: Минимальное количество заголовков
            max_count: Максимальное количество заголовков

        Returns:
            Список объектов Headline
        """
        if min_count is None:
            min_count = settings.HEADLINES_MIN
        if max_count is None:
            max_count = settings.HEADLINES_MAX

        ai_logger.info(f"Генерация заголовков для {len(angles)} углов")

        angles_text = self._format_angles_for_prompt(angles)

        prompt = f"""Ты — копирайтер, специалист по рекламным заголовкам.

Твоя задача: создать {min_count}-{max_count} цепляющих заголовков для маркетинговых углов.

УГЛЫ:
{angles_text}

Для каждого угла создай 3-5 заголовков в РАЗНЫХ форматах.

ФОРМАТЫ ЗАГОЛОВКОВ:
- вопрос: "Почему X? Ответ вас удивит"
- шок: "X делает Y — эксперты в шоке"
- цифра: "X вырос на 300%: что это значит для вас"
- цитата: "Эксперт: 'X изменит всё'"
- интрига: "То, что скрывают о X"
- призыв: "Сделайте X, пока не поздно"

ТРЕБОВАНИЯ:
- Длина: 40-80 символов
- Эмоциональный крючок
- Конкретика (цифры, факты)
- Без кликбейта (честность)

Для каждого заголовка верни JSON объект:
{{
  "id": <номер заголовка 1, 2, 3...>,
  "angle_id": <ID угла>,
  "text": "<текст заголовка>",
  "format": "<формат: вопрос / шок / цифра / цитата / интрига / призыв>",
  "length": <длина в символах>
}}

Верни ТОЛЬКО валидный JSON массив:
[{{"id": 1, ...}}, {{"id": 2, ...}}]"""

        try:
            response_text = await self._call_ai(prompt, temperature=0.8)
            headlines_data = self._parse_json_response(response_text)

            headlines = []
            for data in headlines_data[:max_count]:
                headline = Headline(
                    id=data["id"],
                    angle_id=data["angle_id"],
                    text=data["text"],
                    format=data["format"],
                    length=data.get("length", len(data["text"]))
                )
                headlines.append(headline)

            ai_logger.info(f"Создано {len(headlines)} заголовков")
            return headlines

        except Exception as e:
            ai_logger.error(f"Ошибка генерации заголовков: {e}", exc_info=True)
            raise

    def _format_news_for_prompt(self, news_items: List[RawNews]) -> str:
        """Форматирование новостей для промпта."""
        lines = []
        for i, news in enumerate(news_items, 1):
            lines.append(f"{i}. {news.title}")
            lines.append(f"   Источник: {news.source}")
            lines.append(f"   Дата: {news.date}")
            lines.append(f"   URL: {news.url}")
            if news.snippet:
                lines.append(f"   Описание: {news.snippet[:200]}")
            lines.append("")
        return "\n".join(lines)

    def _format_inforeasons_for_prompt(self, inforeasons: List[InfoReason]) -> str:
        """Форматирование инфоповодов для промпта."""
        lines = []
        for ir in inforeasons:
            lines.append(f"ID {ir.id}: {ir.title}")
            lines.append(f"  Категория: {ir.category}")
            lines.append(f"  Триггер: {ir.emotional_trigger}")
            lines.append(f"  Описание: {ir.description}")
            lines.append("")
        return "\n".join(lines)

    def _format_angles_for_prompt(self, angles: List[Angle]) -> str:
        """Форматирование углов для промпта."""
        lines = []
        for angle in angles:
            lines.append(f"ID {angle.id}: {angle.angle_text}")
            lines.append(f"  Боль: {angle.target_pain}")
            lines.append(f"  Связь с оффером: {angle.offer_connection}")
            lines.append("")
        return "\n".join(lines)

    async def _call_ai(self, prompt: str, temperature: float = 0.7) -> str:
        """Универсальный вызов AI провайдера."""
        ai_logger.debug(
            f"Вызов AI: провайдер={self.provider}, temperature={temperature}")

        if self.provider == "claude":
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        elif self.provider == "gemini":
            response = self.client.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS,
                }
            )
            return response.text

    def _parse_json_response(self, response_text: str) -> list:
        """Парсинг JSON из ответа AI."""
        try:
            # Попытка найти JSON в ответе
            start = response_text.find("[")
            end = response_text.rfind("]") + 1

            if start == -1 or end == 0:
                raise ValueError("JSON массив не найден в ответе")

            json_text = response_text[start:end]
            data = json.loads(json_text)

            if not isinstance(data, list):
                raise ValueError("Ответ не является JSON массивом")

            return data

        except json.JSONDecodeError as e:
            ai_logger.error(f"Ошибка парсинга JSON: {e}")
            ai_logger.debug(f"Ответ AI: {response_text[:500]}")
            raise ValueError(f"Не удалось распарсить JSON: {e}")
