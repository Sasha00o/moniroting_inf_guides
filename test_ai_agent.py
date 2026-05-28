import asyncio
from core.news_parser import aggregate_news
from core.ai_agent import AIAgent
from utils.logger import setup_logging


async def main():
    setup_logging()

    print("\n=== Тест AI агента ===\n")

    # 1. Собираем новости
    print("1. Сбор новостей для BR...")
    news_items = await aggregate_news("BR", days_back=3)
    print(f"   Найдено {len(news_items)} новостей\n")

    # 2. Инициализируем AI агента
    print("2. Инициализация AI агента...")
    agent = AIAgent()
    print(f"   Провайдер: {agent.provider}\n")

    # 3. Классификация инфоповодов
    print("3. Классификация инфоповодов (это займет ~30-60 сек)...")
    inforeasons = await agent.classify_inforeasons(
        news_items=news_items[:20],  # Берем первые 20 новостей для теста
        geo="BR",
        min_count=5,
        max_count=10
    )
    print(f"   Создано {len(inforeasons)} инфоповодов\n")

    # Выводим результаты
    print("=== ИНФОПОВОДЫ ===\n")
    for ir in inforeasons[:3]:
        print(f"ID {ir.id}: {ir.title}")
        print(f"  Категория: {ir.category}")
        print(f"  Триггер: {ir.emotional_trigger}")
        print(f"  Срочность: {ir.urgency}")
        print(f"  Описание: {ir.description}")
        print()

    # 4. Генерация углов
    print("4. Генерация маркетинговых углов...")
    angles = await agent.generate_angles(
        inforeasons=inforeasons[:3],  # Берем первые 3 инфоповода
        offer_description="Финансовые услуги: кредиты, инвестиции, страхование",
        min_count=5,
        max_count=10
    )
    print(f"   Создано {len(angles)} углов\n")

    print("=== УГЛЫ ===\n")
    for angle in angles[:3]:
        print(f"ID {angle.id}: {angle.angle_text}")
        print(f"  Инфоповод: #{angle.inforeason_id}")
        print(f"  Боль: {angle.target_pain}")
        print(f"  Приоритет: {angle.priority}")
        print()

    # 5. Генерация заголовков
    print("5. Генерация заголовков...")
    headlines = await agent.generate_headlines(
        angles=angles[:2],  # Берем первые 2 угла
        min_count=6,
        max_count=10
    )
    print(f"   Создано {len(headlines)} заголовков\n")

    print("=== ЗАГОЛОВКИ ===\n")
    for headline in headlines:
        print(f"ID {headline.id} (угол #{headline.angle_id}): {headline.text}")
        print(f"  Формат: {headline.format}, Длина: {headline.length} символов")
        print()

    print("\n✅ Тест завершен успешно!")


if __name__ == "__main__":
    asyncio.run(main())
