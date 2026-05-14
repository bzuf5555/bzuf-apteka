"""
Search Agent — Qidiruv natijalarini formatlaydi.
Hozir ochiq/yopiq + narq diapazoni + generic muqobil.
"""
from __future__ import annotations
import json
from loguru import logger
from bot.agents import token_saver

SYSTEM_PROMPT = """Sen O'zbekistonlik dorixona qidiruv botining yordamchisisisan.
Dorixona ro'yxatini o'zbekcha qisqa va aniq matn qilib yoz.
Har birida: nom, manzil, narx (taxminiy), masofa, ochiq/yopiq holati.
Oxirida narxlar taxminiy ekanligini bir marta eslatma.
FAQAT matn qaytarish kerak, JSON emas."""


async def format_results(pharmacies: list[dict], medicine_name: str) -> str:
    if not pharmacies:
        return (
            f"😔 Yaqin atrofda <b>{medicine_name}</b> topilmadi.\n\n"
            "💡 Maslahatlar:\n"
            "• Dori nomini boshqacha yozib ko'ring\n"
            "• Generic nomini sinab ko'ring\n"
            "• Qidiruv masofasini kengaytirish mumkin"
        )

    if len(pharmacies) <= 3:
        return _format_simple(pharmacies, medicine_name)

    try:
        payload = json.dumps(
            [{
                "name": p["name"],
                "address": p["address"],
                "price_uzs": p["price"],
                "distance_km": p["distance_km"],
                "is_open": p.get("is_open", True),
                "hours": p.get("open_status", p.get("working_hours", "")),
                "phone": p.get("phone", ""),
            } for p in pharmacies[:10]],
            ensure_ascii=False,
        )
        result = await token_saver.call(
            system=SYSTEM_PROMPT,
            user_message=f"Dori: {medicine_name}\n\nDorixonalar:\n{payload}",
            task_description="format search results pharmacy uzbek open status",
            max_tokens=700,
            temperature=0.3,
        )
        return result
    except Exception as e:
        logger.warning(f"Search agent xatosi: {e}")
        return _format_simple(pharmacies, medicine_name)


def _format_simple(pharmacies: list[dict], medicine_name: str) -> str:
    open_count = sum(1 for p in pharmacies if p.get("is_open", True))
    lines = [f"💊 <b>{medicine_name}</b> — {len(pharmacies)} ta dorixona\n"]

    for i, p in enumerate(pharmacies, 1):
        price = int(p["price"])
        price_lo = int(price * 0.90 // 500 * 500)
        price_hi = int(price * 1.10 // 500 * 500 + 500)
        open_status = p.get("open_status", "")
        phone_line = f"   📞 {p['phone']}\n" if p.get("phone") else ""

        lines.append(
            f"{i}. <b>{p['name']}</b> {open_status}\n"
            f"   📍 {p['address']}\n"
            f"   💰 {price_lo:,}–{price_hi:,} so'm\n"
            f"   📏 {p['distance_km']} km\n"
            f"{phone_line}"
        )

    if open_count < len(pharmacies):
        lines.append(f"\n🟢 <b>{open_count} ta hozir ochiq</b>")

    lines.append("\n<i>⚠️ Narxlar taxminiy. Aniq narq uchun dorixonaga murojaat qiling.</i>")
    return "\n".join(lines)


def format_generic_alternatives(alternatives: list[dict], current_medicine: str) -> str:
    """Generic muqobil bo'limini formatlaydi."""
    if not alternatives:
        return ""

    lines = [f"\n💡 <b>Arzon muqobil ({current_medicine} o'rniga):</b>"]
    for alt in alternatives:
        mn = alt.get("price_min", 0)
        mx = alt.get("price_max", 0)
        if mn and mx:
            lines.append(f"   ⚡ {alt['name_uz']} — {mn:,}–{mx:,} so'm")
        else:
            lines.append(f"   ⚡ {alt['name_uz']}")

    return "\n".join(lines)
