import asyncio
import sys
from core.news_parser import aggregate_news
from utils.logger import setup_logging

# Исправление кодировки для Windows консоли
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


async def main():
    setup_logging()

    # Тест парсинга для BR
    print("\n=== Тест парсера новостей для BR ===\n")
    news_items = await aggregate_news("BR", days_back=3)

    print(f"\nНайдено {len(news_items)} новостей для BR:")
    for i, news in enumerate(news_items[:5], 1):
        print(f"\n{i}. {news.title}")
        print(f"   Источник: {news.source}")
        print(f"   Дата: {news.date}")
        print(f"   URL: {news.url}")
        if news.snippet:
            snippet = news.snippet[:100] + "..." if len(news.snippet) > 100 else news.snippet
            print(f"   Описание: {snippet}")


if __name__ == "__main__":
    asyncio.run(main())
