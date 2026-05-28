import asyncio
import json
import re
from typing import Any

from config import settings
from database.models import (
    Angle,
    Headline,
    InfoReason,
    RawNews,
    Recommendation,
    Risk,
)
from utils.helpers import format_geo_title, validate_geo
from utils.logger import ai_logger

# Сколько новостей отдавать в один промпт классификации (лимит токенов)
MAX_NEWS_IN_CLASSIFY_PROMPT = 30

# source_url берётся из новости по news_index, не из ответа AI
_INFOREASON_FIELDS = (
    "title",
    "date",
    "category",
    "description",
    "emotional_trigger",
    "urgency",
)
_ANGLE_FIELDS = (
    "inforeason_id",
    "angle_text",
    "offer_connection",
    "target_pain",
    "creative_type",
    "priority",
)
_HEADLINE_FIELDS = ("angle_id", "text", "format")


class AIAgent:
    """AI-агент: классификация новостей, углы, заголовки, риски, приоритизация."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        ai_logger.info(
            f"Инициализация AI: провайдер={self.provider}, "
            f"модель={settings.ACTIVE_AI_MODEL}"
        )

        api_key = settings.ACTIVE_AI_KEY

        if self.provider == "claude":
            from anthropic import Anthropic

            self.client = Anthropic(api_key=api_key)
        elif self.provider == "openai":
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key)
            self._chat_model = settings.OPENAI_MODEL
        elif self.provider == "groq":
            from openai import OpenAI

            self.client = OpenAI(
                api_key=api_key,
                base_url=settings.GROQ_BASE_URL,
            )
            self._chat_model = settings.GROQ_MODEL
        elif self.provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(settings.GEMINI_MODEL)
        else:
            raise ValueError(f"Неподдерживаемый AI провайдер: {self.provider}")

    async def classify_inforeasons(
        self,
        news_items: list[RawNews],
        geo: str,
        min_count: int | None = None,
        max_count: int | None = None,
    ) -> list[InfoReason]:
        geo = validate_geo(geo)
        min_count = min_count if min_count is not None else settings.INFOREASONS_MIN
        max_count = max_count if max_count is not None else settings.INFOREASONS_MAX

        if not news_items:
            ai_logger.warning(f"Нет новостей для классификации ({geo})")
            return []

        # Индекс 1..N для привязки source_url к исходной новости
        batch = news_items[:MAX_NEWS_IN_CLASSIFY_PROMPT]
        if len(news_items) > len(batch):
            ai_logger.warning(
                f"В промпт передано {len(batch)} из {len(news_items)} новостей "
                f"(лимит {MAX_NEWS_IN_CLASSIFY_PROMPT})"
            )

        ai_logger.info(
            f"Классификация {len(batch)} новостей → {min_count}-{max_count} "
            f"инфоповодов ({geo})"
        )

        geo_title = format_geo_title(geo)
        news_text = self._format_news_for_prompt(batch)

        prompt = f"""Ты — эксперт по маркетингу и анализу новостей для {geo_title}.

Проанализируй новости и выбери {min_count}–{max_count} самых сильных инфоповодов для маркетинговых кампаний.

КРИТЕРИИ: эмоциональный триггер, свежесть, связь с офферами (финансы, недвижимость, образование, здоровье), охват аудитории.

НОВОСТИ (у каждой есть news_index — используй его для привязки):
{news_text}

Верни JSON-массив. Каждый объект:
{{
  "news_index": <номер новости из списка>,
  "title": "<заголовок инфоповода>",
  "source_type": "<топовое СМИ / локальный таблоид / соцсети / форум>",
  "date": "<YYYY-MM-DD>",
  "category": "<экономика / политика / соцсети / селеба / скандал / банки-налоги / страхи / технологии / здоровье>",
  "description": "<2–3 предложения>",
  "emotional_trigger": "<деньги / кризис / возможность / страх / доверие / FOMO>",
  "urgency": "<срочно 24-48ч / неделя / более>"
}}

Только JSON-массив, без markdown и пояснений."""

        response_text = await self._call_ai(prompt, temperature=0.3)
        raw_items = self._parse_json_response(response_text)
        news_by_index = {i: n for i, n in enumerate(batch, 1)}

        inforeasons: list[InfoReason] = []
        for seq, item in enumerate(raw_items[:max_count], 1):
            try:
                data = self._require_fields(item, _INFOREASON_FIELDS)
            except ValueError as e:
                ai_logger.warning(f"Пропуск инфоповода: {e}")
                continue

            news_index = item.get("news_index")
            if news_index is not None:
                try:
                    news_index = int(news_index)
                except (TypeError, ValueError):
                    news_index = None

            source_news = news_by_index.get(news_index) if news_index else None
            source_url = (
                source_news.url if source_news else str(item.get("source_url", "")).strip()
            )
            if not source_url:
                ai_logger.warning(
                    f"Пропуск инфоповода: нет news_index ({item.get('news_index')!r}) "
                    f"и source_url для «{data.get('title', '')[:50]}»"
                )
                continue

            inforeasons.append(
                InfoReason(
                    id=seq,
                    title=data["title"],
                    source_url=source_url,
                    source_type=data.get("source_type", "неизвестно"),
                    date=data["date"],
                    category=data["category"],
                    description=data["description"],
                    emotional_trigger=data["emotional_trigger"],
                    urgency=data["urgency"],
                )
            )

        ai_logger.info(f"Создано {len(inforeasons)} инфоповодов")
        return inforeasons

    async def generate_angles(
        self,
        inforeasons: list[InfoReason],
        offer_description: str | None = None,
        min_count: int | None = None,
        max_count: int | None = None,
    ) -> list[Angle]:
        min_count = min_count if min_count is not None else settings.ANGLES_MIN
        max_count = max_count if max_count is not None else settings.ANGLES_MAX

        if not inforeasons:
            return []

        ai_logger.info(f"Генерация {min_count}-{max_count} углов для {len(inforeasons)} инфоповодов")

        offer_text = (
            f"\n\nОПИСАНИЕ ОФФЕРА:\n{offer_description}" if offer_description else ""
        )
        prompt = f"""Ты — креативный маркетолог. Создай {min_count}–{max_count} маркетинговых углов.

ИНФОПОВОДЫ:
{self._format_inforeasons_for_prompt(inforeasons)}{offer_text}

На каждый инфоповод — 2–3 угла с разным подходом.
inforeason_id — только ЧИСЛО из поля inforeason_id в списке (например 1, 2), не строка "ID 1".

JSON-массив объектов:
{{
  "inforeason_id": <число>,
  "angle_text": "<формулировка>",
  "offer_connection": "<связь с оффером>",
  "target_pain": "<боль аудитории>",
  "creative_type": "<новостной / эмоциональный / разоблачение / личная история / сравнение>",
  "priority": "<A / B / C>"
}}

Только JSON-массив."""

        response_text = await self._call_ai(prompt, temperature=0.7)
        raw_items = self._parse_json_response(response_text)
        valid_ir_ids = {ir.id for ir in inforeasons}

        angles: list[Angle] = []
        for seq, item in enumerate(raw_items[:max_count], 1):
            try:
                data = self._require_fields(item, _ANGLE_FIELDS)
            except ValueError as e:
                ai_logger.warning(f"Пропуск угла: {e}")
                continue

            ir_id = self._parse_ai_id(data["inforeason_id"], "inforeason_id")
            if ir_id is None or ir_id not in valid_ir_ids:
                ai_logger.warning(f"Пропуск угла: неизвестный inforeason_id={ir_id}")
                continue

            angles.append(
                Angle(
                    id=seq,
                    inforeason_id=ir_id,
                    angle_text=data["angle_text"],
                    offer_connection=data["offer_connection"],
                    target_pain=data["target_pain"],
                    creative_type=data["creative_type"],
                    priority=data["priority"],
                )
            )

        ai_logger.info(f"Создано {len(angles)} углов")
        return angles

    async def generate_headlines(
        self,
        angles: list[Angle],
        min_count: int | None = None,
        max_count: int | None = None,
    ) -> list[Headline]:
        min_count = min_count if min_count is not None else settings.HEADLINES_MIN
        max_count = max_count if max_count is not None else settings.HEADLINES_MAX

        if not angles:
            return []

        ai_logger.info(f"Генерация заголовков для {len(angles)} углов")

        prompt = f"""Ты — копирайтер. Создай {min_count}–{max_count} рекламных заголовков.

УГЛЫ:
{self._format_angles_for_prompt(angles)}

На каждый угол — 3–5 заголовков в разных форматах (вопрос, шок, цифра, цитата, интрига, призыв).
Длина 40–80 символов.
angle_id — только ЧИСЛО из поля angle_id в списке (например 1, 2), не строка "ID 1".

JSON-массив:
{{
  "angle_id": <число>,
  "text": "<заголовок>",
  "format": "<формат>"
}}

Только JSON-массив."""

        response_text = await self._call_ai(prompt, temperature=0.8)
        raw_items = self._parse_json_response(response_text)
        valid_angle_ids = {a.id for a in angles}

        headlines: list[Headline] = []
        for seq, item in enumerate(raw_items[:max_count], 1):
            try:
                data = self._require_fields(item, _HEADLINE_FIELDS)
            except ValueError as e:
                ai_logger.warning(f"Пропуск заголовка: {e}")
                continue

            angle_id = self._parse_ai_id(data["angle_id"], "angle_id")
            if angle_id is None or angle_id not in valid_angle_ids:
                ai_logger.warning(
                    f"Пропуск заголовка: неверный angle_id={data['angle_id']!r}"
                )
                continue

            text = data["text"]
            headlines.append(
                Headline(
                    id=seq,
                    angle_id=angle_id,
                    text=text,
                    format=data["format"],
                    length=self._parse_ai_int(item.get("length"), default=len(text)),
                )
            )

        ai_logger.info(f"Создано {len(headlines)} заголовков")
        return headlines

    async def assess_risks(
        self,
        inforeasons: list[InfoReason],
    ) -> list[Risk]:
        """Оценка рисков по инфоповодам (блок 5 отчёта)."""
        if not inforeasons:
            return []

        ai_logger.info(f"Оценка рисков для {len(inforeasons)} инфоповодов")

        lines = [
            f"ID {ir.id}: {ir.title} ({ir.category}, триггер: {ir.emotional_trigger})"
            for ir in inforeasons
        ]
        prompt = f"""Ты — юрист и compliance-эксперт рекламы.

Оцени риски для каждого инфоповода:

{chr(10).join(lines)}

JSON-массив (inforeason_id из списка):
{{
  "inforeason_id": <ID>,
  "legal_risk": "<низкий / средний / высокий + пояснение>",
  "platform_ban_risk": "<оценка>",
  "audience_backlash_risk": "<оценка>",
  "reputation_risk": "<оценка>",
  "expiry_time": "<когда тема протухнет>"
}}

Только JSON-массив."""

        response_text = await self._call_ai(prompt, temperature=0.3)
        raw_items = self._parse_json_response(response_text)
        valid_ids = {ir.id for ir in inforeasons}

        risks: list[Risk] = []
        for item in raw_items:
            ir_id = self._parse_ai_id(item.get("inforeason_id"), "inforeason_id")
            if ir_id is None or ir_id not in valid_ids:
                continue
            risks.append(
                Risk(
                    inforeason_id=ir_id,
                    legal_risk=item.get("legal_risk", "не оценено"),
                    platform_ban_risk=item.get("platform_ban_risk", "не оценено"),
                    audience_backlash_risk=item.get(
                        "audience_backlash_risk", "не оценено"
                    ),
                    reputation_risk=item.get("reputation_risk", "не оценено"),
                    expiry_time=item.get("expiry_time", "неизвестно"),
                )
            )

        ai_logger.info(f"Оценено рисков: {len(risks)}")
        return risks

    async def prioritize_ideas(
        self,
        angles: list[Angle],
        inforeasons: list[InfoReason],
        offer_description: str | None = None,
        top_count: int | None = None,
    ) -> list[Recommendation]:
        """Топ-N идей для теста (блок 4 отчёта)."""
        top_count = top_count if top_count is not None else settings.TOP_IDEAS_COUNT
        if not angles:
            return []

        ai_logger.info(f"Приоритизация топ-{top_count} из {len(angles)} углов")

        ir_map = {ir.id: ir for ir in inforeasons}
        lines = []
        for angle in angles:
            ir = ir_map.get(angle.inforeason_id)
            trigger = ir.emotional_trigger if ir else "—"
            lines.append(
                f"angle_id {angle.id}: {angle.angle_text} "
                f"(инфоповод #{angle.inforeason_id}, триггер: {trigger}, "
                f"приоритет: {angle.priority})"
            )

        offer_text = f"\nОффер: {offer_description}" if offer_description else ""
        prompt = f"""Выбери топ-{top_count} идей для A/B теста.

{chr(10).join(lines)}{offer_text}

JSON-массив:
{{
  "rank": <1..{top_count}>,
  "angle_id": <ID угла>,
  "reasoning": "<обоснование>",
  "freshness_score": <1-10>,
  "trigger_strength_score": <1-10>,
  "offer_fit_score": <1-10>,
  "top_headlines": []
}}

Только JSON-массив."""

        response_text = await self._call_ai(prompt, temperature=0.3)
        raw_items = self._parse_json_response(response_text)
        valid_angle_ids = {a.id for a in angles}

        recommendations: list[Recommendation] = []
        for item in raw_items[:top_count]:
            angle_id = self._parse_ai_id(item.get("angle_id"), "angle_id")
            if angle_id is None or angle_id not in valid_angle_ids:
                continue
            recommendations.append(
                Recommendation(
                    rank=self._parse_ai_int(
                        item.get("rank"), default=len(recommendations) + 1
                    ),
                    angle_id=angle_id,
                    reasoning=item.get("reasoning", ""),
                    freshness_score=self._parse_ai_int(
                        item.get("freshness_score"), default=5
                    ),
                    trigger_strength_score=self._parse_ai_int(
                        item.get("trigger_strength_score"), default=5
                    ),
                    offer_fit_score=self._parse_ai_int(
                        item.get("offer_fit_score"), default=5
                    ),
                    top_headlines=item.get("top_headlines", []),
                )
            )

        recommendations.sort(key=lambda r: r.rank)
        ai_logger.info(f"Топ рекомендаций: {len(recommendations)}")
        return recommendations

    def _format_news_for_prompt(self, news_items: list[RawNews]) -> str:
        lines = []
        for i, news in enumerate(news_items, 1):
            lines.append(f"news_index: {i}")
            lines.append(f"  title: {news.title}")
            lines.append(f"  source: {news.source}")
            lines.append(f"  date: {news.date}")
            lines.append(f"  url: {news.url}")
            if news.snippet:
                lines.append(f"  snippet: {news.snippet[:300]}")
            lines.append("")
        return "\n".join(lines)

    def _format_inforeasons_for_prompt(self, inforeasons: list[InfoReason]) -> str:
        lines = []
        for ir in inforeasons:
            lines.append(f"inforeason_id: {ir.id} | {ir.title}")
            lines.append(f"  category: {ir.category}")
            lines.append(f"  trigger: {ir.emotional_trigger}")
            lines.append(f"  urgency: {ir.urgency}")
            lines.append(f"  description: {ir.description}")
            lines.append("")
        return "\n".join(lines)

    def _format_angles_for_prompt(self, angles: list[Angle]) -> str:
        lines = []
        for angle in angles:
            lines.append(
                f"angle_id: {angle.id} | инфоповод {angle.inforeason_id} | {angle.angle_text}"
            )
            lines.append(f"  pain: {angle.target_pain}")
            lines.append(f"  offer: {angle.offer_connection}")
            lines.append("")
        return "\n".join(lines)

    async def _call_ai(self, prompt: str, temperature: float = 0.7) -> str:
        ai_logger.debug(
            f"AI call: provider={self.provider}, temp={temperature}, "
            f"prompt_len={len(prompt)}"
        )
        return await asyncio.to_thread(self._call_ai_sync, prompt, temperature)

    def _call_openai_compatible_chat(self, prompt: str, temperature: float) -> str:
        """Chat Completions для OpenAI и Groq (один и тот же SDK)."""
        from openai import APIError, AuthenticationError, RateLimitError

        try:
            response = self.client.chat.completions.create(
                model=self._chat_model,
                max_tokens=settings.ACTIVE_AI_MAX_TOKENS,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except AuthenticationError as e:
            raise ValueError(
                f"Неверный API-ключ {self.provider.upper()}. "
                f"Проверьте {'GROQ_API_KEY' if self.provider == 'groq' else 'OPENAI_API_KEY'} в .env"
            ) from e
        except RateLimitError as e:
            raise ValueError(
                f"Лимит запросов {self.provider.upper()} исчерпан. "
                "Подождите или смените AI_PROVIDER в .env"
            ) from e
        except APIError as e:
            raise ValueError(
                f"Ошибка API {self.provider.upper()}: {getattr(e, 'message', e)}"
            ) from e

    def _call_ai_sync(self, prompt: str, temperature: float) -> str:
        if self.provider == "claude":
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.ACTIVE_AI_MAX_TOKENS,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        if self.provider in ("openai", "groq"):
            return self._call_openai_compatible_chat(prompt, temperature)

        if self.provider == "gemini":
            response = self.client.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS,
                    "response_mime_type": "application/json",
                },
            )
            if not response.candidates:
                raise ValueError("Gemini: пустой ответ (блокировка или лимит)")
            return response.text or ""

        raise ValueError(f"Неизвестный провайдер: {self.provider}")

    def _parse_json_response(self, response_text: str) -> list[dict[str, Any]]:
        text = response_text.strip()
        # Убрать markdown-обёртку ```json ... ```
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence:
            text = fence.group(1).strip()

        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end <= start:
            # OpenAI json_object — один объект с ключом-массивом
            obj_start = text.find("{")
            obj_end = text.rfind("}") + 1
            if obj_start != -1 and obj_end > obj_start:
                obj = json.loads(text[obj_start:obj_end])
                if isinstance(obj, list):
                    return obj
                for value in obj.values():
                    if isinstance(value, list):
                        return value
            raise ValueError("JSON-массив не найден в ответе AI")

        data = json.loads(text[start:end])
        if not isinstance(data, list):
            raise ValueError("Ответ AI не является JSON-массивом")
        return data

    @staticmethod
    def _require_fields(item: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
        missing = [f for f in fields if not item.get(f)]
        if missing:
            raise ValueError(f"нет полей: {', '.join(missing)}")
        return item

    @staticmethod
    def _parse_ai_id(value: Any, field_name: str = "id") -> int | None:
        """
        Разбор ID из ответа AI: 1, "1", "ID 1", "#2" → int.
        """
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)

        text = str(value).strip()
        if text.isdigit():
            return int(text)

        match = re.search(r"\d+", text)
        if match:
            return int(match.group())

        ai_logger.warning(f"Не удалось разобрать {field_name}: {value!r}")
        return None

    @staticmethod
    def _parse_ai_int(value: Any, default: int = 0) -> int:
        if value is None:
            return default
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        text = str(value).strip()
        if text.isdigit():
            return int(text)
        match = re.search(r"\d+", text)
        if match:
            return int(match.group())
        return default
