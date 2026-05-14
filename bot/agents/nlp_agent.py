"""
NLP Agent — Dori nomlarini normallashtiradi.

Foydalanuvchi yozishi mumkin:
  - "paracetamol", "Paracetamol", "парацетамол", "paratsetamol"
  - "aspirin 500mg", "aspirin tabletkasi"
  - Imloviy xatolar: "parasetamol", "aspiryn"

Bu agent nomi toza qiladi → DB qidiruvi aniqroq bo'ladi.
"""

from __future__ import annotations
import json
from loguru import logger
from bot.agents import token_saver

SYSTEM_PROMPT = """Sen O'zbekistondagi farmatsevtik nomlarni normallashtiruvchi assistent.

Foydalanuvchi dori nomini yozadi (o'zbek, rus yoki lotincha, imlo xatolari bilan).

Vazifang:
1. Dori nomining asosiy generic nomini aniqlash
2. Imloviy xatolarni tuzatish
3. Dozani (mg, ml) ajratish
4. JSON formatida qaytarish

DOIM quyidagi JSON formatini qaytarish:
{
  "generic_name": "paracetamol",
  "search_terms": ["paracetamol", "парацетамол", "acetaminophen"],
  "dose": "500mg",
  "confidence": 0.95
}

Agar noma'lum bo'lsa:
{
  "generic_name": null,
  "search_terms": ["<original_query>"],
  "dose": null,
  "confidence": 0.1
}"""


async def normalize_medicine_name(query: str) -> dict:
    """
    Dori nomini normallashtiradi.

    Returns:
        {generic_name, search_terms, dose, confidence}
    """
    if not query or len(query.strip()) < 2:
        return {"generic_name": None, "search_terms": [query], "dose": None, "confidence": 0.0}

    try:
        raw = await token_saver.call(
            system=SYSTEM_PROMPT,
            user_message=f"Dori nomi: {query.strip()}",
            task_description="normalize translate medicine name",
            max_tokens=200,
            temperature=0.1,
        )
        result = json.loads(raw.strip())
        logger.debug(f"NLP normalize: '{query}' → {result}")
        return result
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"NLP agent xatosi ({query}): {e} — fallback ishlatiladi")
        return {
            "generic_name": query.lower().strip(),
            "search_terms": [query.lower().strip()],
            "dose": None,
            "confidence": 0.5,
        }
