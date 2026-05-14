"""
Brand Agent — Noma'lum dori nomini generic nomiga aylantiradi.
"Mexidol" → "ethylmethylhydroxypyridine"
"Pentalgin" → "paracetamol"
"Terzhinan" → "metronidazole"

Bu agent DB da topilmagan dorilar uchun fallback vazifasini o'taydi.
Haiku (arzon, tez) modeli ishlatiladi.
"""
import json
from loguru import logger
from bot.agents import token_saver

SYSTEM_PROMPT = """Sen farmatsevt yordamchisisisan.
Senga dori nomi beriladi. Sen uning asosiy aktiv moddasi (generic name) ni inglizchada qaytarasan.
Kombinatsiyali dorida eng asosiy moddani qaytarasan.

Javob faqat JSON:
{"generic": "paracetamol", "is_medicine": true, "confidence": 0.9}

Dori emas (alomat, savol) bo'lsa:
{"generic": null, "is_medicine": false, "confidence": 0.0}

Misol:
- "Mexidol" → {"generic": "ethylmethylhydroxypyridine succinate", "is_medicine": true, "confidence": 0.95}
- "Pentalgin" → {"generic": "paracetamol", "is_medicine": true, "confidence": 0.8}
- "No-Shpa" → {"generic": "drotaverine", "is_medicine": true, "confidence": 0.99}
- "Boshim og'riyapti" → {"generic": null, "is_medicine": false, "confidence": 0.0}"""


async def get_generic_name(brand_name: str) -> dict:
    """
    Brand nomini generic nomga aylantiradi.
    Returns: {generic: str|None, is_medicine: bool, confidence: float}
    """
    try:
        raw = await token_saver.call(
            system=SYSTEM_PROMPT,
            user_message=brand_name.strip(),
            task_description="identify medicine generic name",
            max_tokens=80,
            temperature=0.1,
        )
        result = json.loads(raw.strip())
        logger.debug(f"Brand agent: '{brand_name}' → {result}")
        return result
    except Exception as e:
        logger.warning(f"Brand agent xatosi ({brand_name}): {e}")
        return {"generic": None, "is_medicine": False, "confidence": 0.0}
