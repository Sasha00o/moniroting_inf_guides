import asyncio
from anthropic import Anthropic
from config import settings


async def test_claude_api():
    """Простой тест Claude API."""
    print(f"Тестирование Claude API...")
    print(f"Модель: {settings.CLAUDE_MODEL}")
    print(f"API ключ: {settings.CLAUDE_API_KEY[:20]}...")

    try:
        client = Anthropic(api_key=settings.CLAUDE_API_KEY)

        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Скажи привет на русском языке одним предложением."
            }]
        )

        print(f"\n✅ API работает!")
        print(f"Ответ: {response.content[0].text}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print(f"Тип ошибки: {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(test_claude_api())
