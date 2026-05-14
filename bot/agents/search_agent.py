"""
Search Agent — Qidiruv natijalarini tahlil qiladi va foydalanuvchiga qulay matn hosil qiladi.
Agar natija ko'p bo'lsa — eng yaxshilarini tanlaydi.
"""

from __future__ import annotations
import json
from loguru import logger
from bot.agents import token_saver

SYSTEM_PROMPT = """Sen dorixona qidiruv botining assistent dasturiSan.
Senga JSON formatida dorixona ro'yxati beriladi.
Foydalanuvchiga eng foydali, qisqa va aniq O'zbekcha matn tayyorla.

Har bir dorixona uchun:
- Nomi
- Manzil
- Narx (so'm)
- Masofa (km)
- Ish vaqti

Jami 5 ta dan ko'p dorixona bo'lsa, eng yaqin va arzonini tanlash bo'yicha qisqacha maslahat ber.
FAQAT matn qaytarish kerak, JSON emas."""


async def format_results(pharmacies: list[dict], medicine_name: str) -> str:
    """Qidiruv natijalarini foydalanuvchiga qulay matnda formatlaydi."""
    if not pharmacies:
        return (
            f"😔 Afsuski, yaqin atrofda <b>{medicine_name}</b> topilmadi.\n\n"
            "💡 Maslahatlar:\n"
            "• Qidiruv doirasini kengaytirish mumkin\n"
            "• Dori nomini boshqacha yozib ko'ring\n"
            "• Dorixona bilan bog'laning"
        )

    if len(pharmacies) <= 3:
        return _format_simple(pharmacies, medicine_name)

    try:
        payload = json.dumps(
            [
                {
                    "name": p["name"],
                    "address": p["address"],
                    "price": p["price"],
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
            task_description="format search results list pharmacy",
            max_tokens=600,
            temperature=0.4,
        )
        return result
    except Exception as e:
        logger.warning(f"Search agent format xatosi: {e} — fallback")
        return _format_simple(pharmacies, medicine_name)


def _format_simple(pharmacies: list[dict], medicine_name: str) -> str:
    """Claude API siz tez format (< 3 natija)."""
    lines = [f"💊 <b>{medicine_name}</b> topildi!\n"]
    for i, p in enumerate(pharmacies, 1):
        lines.append(
            f"{i}. <b>{p['name']}</b>\n"
            f"   📍 {p['address']}\n"
            f"   💰 {int(p['price']):,} so'm\n"
            f"   📏 {p['distance_km']} km\n"
            f"   🕐 {p.get('working_hours', 'N/A')}\n"
            + (f"   📞 {p['phone']}\n" if p.get("phone") else "")
        )
    return "\n".join(lines)
