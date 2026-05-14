import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.agents.token_saver import call

async def main():
    print("=== Groq testi boshlanmoqda ===\n")

    # 1. NLP normalize
    r1 = await call(
        system="Translate medicine name to generic English. Reply only JSON: {\"generic\": \"name\"}",
        user_message="Paratsetamol",
        task_description="normalize medicine name",
        max_tokens=50,
        temperature=0.1,
    )
    print(f"1. NLP normalize: {r1}")

    # 2. Alomat aniqlash
    r2 = await call(
        system="Detect if this is a symptom (not a medicine name). Reply JSON: {\"is_symptom\": true}",
        user_message="Boshim og'riyapti",
        task_description="detect symptom uzbek",
        max_tokens=50,
        temperature=0.1,
    )
    print(f"2. Alomat test: {r2}")

    # 3. Brand→Generic
    r3 = await call(
        system="What is the generic name of this medicine? Reply JSON: {\"generic\": \"name\", \"is_medicine\": true}",
        user_message="Mexidol",
        task_description="identify medicine generic name",
        max_tokens=80,
        temperature=0.1,
    )
    print(f"3. Brand→Generic: {r3}")

    print("\n=== Barcha testlar muvaffaqiyatli ===")

asyncio.run(main())
