"""Генератор отчетов: оркестрация всех компонентов."""

import asyncio
from datetime import date
from typing import AsyncGenerator, List

from config import settings
from core.ai_agent import AIAgent
from core.news_parser import aggregate_news
from database.models import Report, InfoReason, Angle, Headline, Risk, Recommendation, UrgencyBoard
from database.sheets_manager import SheetsManager
from utils.helpers import validate_geo, news_period, format_period_display
from utils.logger import generator_logger


class ReportGenerator:
    """Главный генератор отчетов."""

    def __init__(self):
        self.ai_agent = AIAgent()
        self.sheets_manager = SheetsManager()

    async def generate_report(
        self,
        geo: str,
        offer_description: str | None = None,
        days_back: int | None = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Генерация полного отчета (параллельная оркестрация с yield статусов).
        
        Yields:
            dict с ключами:
            - stage: название этапа
            - status: статус ('in_progress', 'completed', 'error')
            - progress: прогресс 0-100
            - message: сообщение для пользователя
            - data: данные (отчет, URL, ошибка)
        """
        try:
            geo = validate_geo(geo)
            if days_back is None:
                days_back = settings.NEWS_DAYS_BACK
            
            generator_logger.info(f"Начало генерации отчета для {geo}, период {days_back} дней")
            
            # Этап 1: Парсинг новостей
            yield {
                "stage": "parsing",
                "status": "in_progress",
                "progress": 10,
                "message": f"🔍 Парсинг новостей для {geo}..."
            }
            
            news_items = await aggregate_news(geo, days_back)
            if not news_items:
                generator_logger.warning(f"Нет новостей для {geo}")
                yield {
                    "stage": "parsing",
                    "status": "error",
                    "message": f"❌ Не найдено новостей для {geo}",
                    "data": {"error": "no_news"}
                }
                return
            
            yield {
                "stage": "parsing",
                "status": "completed",
                "progress": 20,
                "message": f"✅ Найдено {len(news_items)} новостей"
            }
            
            # Этап 2: Классификация инфоповодов
            yield {
                "stage": "classification",
                "status": "in_progress",
                "progress": 30,
                "message": f"🤖 AI анализирует {len(news_items)} новостей..."
            }
            
            inforeasons = await self.ai_agent.classify_inforeasons(
                news_items=news_items,
                geo=geo
            )
            
            yield {
                "stage": "classification",
                "status": "completed",
                "progress": 40,
                "message": f"✅ Создано {len(inforeasons)} инфоповодов"
            }
            
            if not inforeasons:
                generator_logger.warning(f"AI не создал инфоповоды для {geo}")
                yield {
                    "stage": "classification",
                    "status": "error",
                    "message": "❌ AI не смог создать инфоповоды",
                    "data": {"error": "no_inforeasons"}
                }
                return
            
            # Этап 3: Генерация углов
            yield {
                "stage": "angles",
                "status": "in_progress",
                "progress": 50,
                "message": "💡 Генерация маркетинговых углов..."
            }
            
            angles = await self.ai_agent.generate_angles(
                inforeasons=inforeasons,
                offer_description=offer_description
            )
            
            yield {
                "stage": "angles",
                "status": "completed",
                "progress": 60,
                "message": f"✅ Создано {len(angles)} углов"
            }
            
            # Этап 4: Генерация заголовков
            yield {
                "stage": "headlines",
                "status": "in_progress",
                "progress": 70,
                "message": "✍️ Создание рекламных заголовков..."
            }
            
            headlines = await self.ai_agent.generate_headlines(
                angles=angles
            )
            
            yield {
                "stage": "headlines",
                "status": "completed",
                "progress": 75,
                "message": f"✅ Создано {len(headlines)} заголовков"
            }
            
            # Этап 5: Оценка рисков
            yield {
                "stage": "risks",
                "status": "in_progress",
                "progress": 80,
                "message": "⚠️ Анализ рисков..."
            }
            
            risks = await self.ai_agent.assess_risks(inforeasons=inforeasons)
            
            yield {
                "stage": "risks",
                "status": "completed",
                "progress": 85,
                "message": f"✅ Проанализировано {len(risks)} рисков"
            }
            
            # Этап 6: Приоритизация идей
            yield {
                "stage": "prioritization",
                "status": "in_progress",
                "progress": 90,
                "message": "🎯 Ранжирование топ-5 идей..."
            }
            
            recommendations = await self.ai_agent.prioritize_ideas(
                angles=angles,
                inforeasons=inforeasons,
                offer_description=offer_description
            )
            
            yield {
                "stage": "prioritization",
                "status": "completed",
                "progress": 93,
                "message": f"✅ Топ-{len(recommendations)} идей готов"
            }
            
            # Этап 7: Построение срочности
            urgency_board = self._build_urgency_board(inforeasons)
            
            # Этап 8: Запись в Google Sheets
            yield {
                "stage": "sheets",
                "status": "in_progress",
                "progress": 95,
                "message": "📊 Создание Google Sheets..."
            }
            
            # Создаем отчет
            period_start, period_end = news_period(days_back)
            report = Report(
                geo=geo,
                date=date.today().isoformat(),
                period_start=period_start.isoformat(),
                period_end=period_end.isoformat(),
                inforeasons=inforeasons,
                angles=angles,
                headlines=headlines,
                risks=risks,
                recommendations=recommendations,
                urgency_board=urgency_board
            )
            
            # Пишем в Google Sheets
            sheet_url = self.sheets_manager.write_report(report)
            
            generator_logger.info(f"Отчет для {geo} готов: {sheet_url}")
            
            yield {
                "stage": "sheets",
                "status": "completed",
                "progress": 100,
                "message": "✅ Отчет готов!",
                "data": {
                    "sheet_url": sheet_url,
                    "geo": geo,
                    "inforeasons_count": len(inforeasons),
                    "angles_count": len(angles),
                    "headlines_count": len(headlines),
                }
            }
            
        except Exception as e:
            generator_logger.exception(f"Ошибка при генерации отчета: {e}")
            yield {
                "stage": "error",
                "status": "error",
                "progress": 0,
                "message": f"❌ Ошибка: {str(e)[:100]}",
                "data": {"error": str(e)}
            }

    def _build_urgency_board(self, inforeasons: List[InfoReason]) -> UrgencyBoard:
        """Построение доски срочности по инфоповодам."""
        urgent_48h = []
        can_wait = []
        
        for ir in inforeasons:
            if "24-48" in ir.urgency or "срочно" in ir.urgency.lower():
                urgent_48h.append(ir.id)
            else:
                can_wait.append(ir.id)
        
        return UrgencyBoard(urgent_48h=urgent_48h, can_wait=can_wait)
