"""
Search Agent — Qidiruv natijalarini formatlaydi.
Narxlar taxminiy ko'rsatiladi (dorixonada farq qilishi mumkin).
"""

from __future__ import annotations
import json
from loguru import logger
from bot.agents import token_saver

SYSTEM_PROMPT = """Sen O'zbekistonlik dorixona qidiruv botining yordamchisisisan.
Senga JSON formatida dorixona ro'yxati beriladi.
Foydalanuvchiga qisqa, aniq O'zbekcha matn tayyorla.

Har bir dorixona uchun:
- Nomi
- Manzil
- Narx (taxminiy, so'mda)
- Masofa
- Ish vaqti

Narx TAXMINIY ekanligi haqida oxirida bir marta eslatma qo'y.
5 dan ko'p bo'lsa — eng yaqin va arzoniga e'tibor qarat.
FAQAT matn qaytarish kerak, JSON emas."""


async def format_results(pharmacies: list[dict], medicine_name: str) -> str:
    if not pharmacies:
        return (
            f"😔 Yaqin atrofda <b>{medicine_name}</b> topilmadi.\n\n"
            "💡 Maslahatlar:\n"
            "• Dori nomini boshqacha yozib ko'ring\n"
            "• Generic (kimyoviy) nomini sinab ko'ring\n"
            "• Qidiruv masofasini kengaytirish mumkin"
        )

    if len(pharmacies) <= 3:
        return _format_simple(pharmacies, medicine_name)

    try:
        payload = json.dumps(
            [
                {
                    "name": p["name"],
                    "address": p["address"],
                    "price_uzs": p["price"],
                    "distance_km": p["distance_km"],
                    "phone": p.get("phone", ""),
                    "hours": p.get("working_hours", ""),
                }
                for p in pharmacies[:10]
            ],
            ensure_ascii=False,
        )
        result = await token_saver.call(
            system=SYSTEM_PROMPT,
            user_message=f"Dori: {medicine_name}\n\nDorixonalar:\n{payload}",
            task_description="format search results list pharmacy uzbek",
            max_tokens=700,
            temperature=0.3,
        )
        return result
    except Exception as e:
        logger.warning(f"Search agent xatosi: {e} — oddiy format")
        return _format_simple(pharmacies, medicine_name)


def _format_simple(pharmacies: list[dict], medicine_name: str) -> str:
    """Claude API siz tez format."""
    lines = [f"💊 <b>{medicine_name}</b> — {len(pharmacies)} ta dorixona topildi\n"]
    for i, p in enumerate(pharmacies, 1):
        price = int(p["price"])
        # Narq diapazoni: ±10% (haqiqiy narx shu chegarada bo'ladi)
        price_lo = int(price * 0.90 // 500 * 500)
        price_hi = int(price * 1.10 // 500 * 500 + 500)

        phone_line = f"   📞 {p['phone']}\n" if p.get("phone") else ""
        lines.append(
            f"{i}. <b>{p['name']}</b>\n"
            f"   📍 {p['address']}\n"
            f"   💰 {price_lo:,}–{price_hi:,} so'm\n"
            f"   📏 {p['distance_km']} km\n"
            f"   🕐 {p.get('working_hours', '—')}\n"
            f"{phone_line}"
        )

    lines.append(
        "\n<i>⚠️ Narxlar taxminiy. Aniq narq uchun dorixonaga murojaat qiling.</i>"
    )
    return "\n".join(lines)
