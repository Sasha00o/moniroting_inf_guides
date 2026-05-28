"""
Mock AI агент для тестирования без реальных API вызовов.
Используется когда нужно протестировать логику без затрат на API.
"""
from typing import List
from database.models import RawNews, InfoReason, Angle, Headline
from utils.logger import ai_logger


class MockAIAgent:
    """Mock AI агент для тестирования."""

    def __init__(self):
        ai_logger.info(
            "Инициализация Mock AI агента (без реальных API вызовов)")

    async def classify_inforeasons(
        self,
        news_items: List[RawNews],
        geo: str,
        min_count: int = 5,
        max_count: int = 10
    ) -> List[InfoReason]:
        """Возвращает mock инфоповоды."""
        ai_logger.info(
            f"Mock: создание {min_count} инфоповодов из {len(news_items)} новостей")

        inforeasons = []
        for i in range(min(min_count, len(news_items))):
            news = news_items[i]
            inforeason = InfoReason(
                id=i + 1,
                title=news.title,
                source_url=news.url,
                source_type="топовое СМИ",
                date=news.date,
                category="экономика",
                description=f"Mock описание для новости: {news.title[:100]}",
                emotional_trigger="деньги",
                urgency="неделя"
            )
            inforeasons.append(inforeason)

        ai_logger.info(f"Mock: создано {len(inforeasons)} инфоповодов")
        return inforeasons

    async def generate_angles(
        self,
        inforeasons: List[InfoReason],
        offer_description: str = None,
        min_count: int = 5,
        max_count: int = 10
    ) -> List[Angle]:
        """Возвращает mock углы."""
        ai_logger.info(
            f"Mock: создание углов для {len(inforeasons)} инфоповодов")

        angles = []
        angle_id = 1

        for ir in inforeasons:
            # 2 угла на каждый инфоповод
            for j in range(2):
                angle = Angle(
                    id=angle_id,
                    inforeason_id=ir.id,
                    angle_text=f"Mock угол {angle_id}: связь с {ir.title[:50]}",
                    offer_connection="Связь с финансовыми услугами",
                    target_pain="Страх упустить выгоду",
                    creative_type="новостной",
                    priority="A" if j == 0 else "B"
                )
                angles.append(angle)
                angle_id += 1

                if len(angles) >= max_count:
                    break

            if len(angles) >= max_count:
                break

        ai_logger.info(f"Mock: создано {len(angles)} углов")
        return angles

    async def generate_headlines(
        self,
        angles: List[Angle],
        min_count: int = 10,
        max_count: int = 30
    ) -> List[Headline]:
        """Возвращает mock заголовки."""
        ai_logger.info(f"Mock: создание заголовков для {len(angles)} углов")

        headlines = []
        headline_id = 1

        formats = ["вопрос", "шок", "цифра", "цитата", "интрига"]

        for angle in angles:
            # 3 заголовка на каждый угол
            for j in range(3):
                text = f"Mock заголовок {headline_id}: {angle.angle_text[:40]}?"
                headline = Headline(
                    id=headline_id,
                    angle_id=angle.id,
                    text=text,
                    format=formats[j % len(formats)],
                    length=len(text)
                )
                headlines.append(headline)
                headline_id += 1

                if len(headlines) >= max_count:
                    break

            if len(headlines) >= max_count:
                break

        ai_logger.info(f"Mock: создано {len(headlines)} заголовков")
        return headlines
