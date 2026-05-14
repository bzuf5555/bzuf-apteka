"""
Symptom Agent — Foydalanuvchi alomat yozadi → dori tavsiyasi.
"Boshim og'riyapti" → [paracetamol, ibuprofen, analgin]
"""
import json
from loguru import logger
from bot.agents import token_saver

SYSTEM_PROMPT = """Sen O'zbekistonlik farmatsevt yordamchisisisan.
Foydalanuvchi alomat yoki shikoyat yozadi (o'zbekcha yoki ruscha).
Sen retseptsiz (OTC) sotiluvchi eng mos dorilarni tavsiya qilasan.

DOIM quyidagi JSON formatini qaytarish:
{
  "is_symptom": true,
  "medicines": ["paracetamol", "ibuprofen"],
  "advice": "Bosh og'rig'i uchun Paracetamol yoki Ibuprofen ichish mumkin."
}

Agar alomat emas, dori nomi bo'lsa:
{"is_symptom": false, "medicines": [], "advice": ""}

Faqat keng tarqalgan, xavfsiz OTC dorilar. Retseptli dori tavsiya qilma.
Jiddiy kasallikda shifokorga murojaat qilishni maslahat ber."""


async def detect_symptom(query: str) -> dict:
    """
    Foydalanuvchi kiritmasidan alomat aniqlaydi.
    Returns: {is_symptom, medicines: list[str], advice: str}
    """
    try:
        raw = await token_saver.call(
            system=SYSTEM_PROMPT,
            user_message=query.strip(),
            task_description="detect symptom suggest medicine uzbek",
            max_tokens=200,
            temperature=0.2,
        )
        result = json.loads(raw.strip())
        logger.debug(f"Symptom agent: '{query}' → {result}")
        return result
    except Exception as e:
        logger.warning(f"Symptom agent xatosi: {e}")
        return {"is_symptom": False, "medicines": [], "advice": ""}
