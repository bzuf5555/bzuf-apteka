"""
Search Agent — Qidiruv natijalarini formatlaydi.
Doim _format_clean() ishlatiladi — tez, barqaror, Groq kerak emas.
"""
from __future__ import annotations
from loguru import logger


async def format_results(pharmacies: list[dict], medicine_name: str) -> str:
    if not pharmacies:
        return (
            f"😔 Yaqin atrofda <b>{medicine_name}</b> topilmadi.\n\n"
            "💡 Maslahatlar:\n"
            "• Dori nomini boshqacha yozib ko'ring\n"
            "• Generic nomini sinab ko'ring"
        )
    return _format_clean(pharmacies, medicine_name)


def _format_clean(pharmacies: list[dict], medicine_name: str) -> str:
    open_count  = sum(1 for p in pharmacies if p.get("is_open", True))
    total       = len(pharmacies)
    open_label  = f"🟢 {open_count} ta ochiq" if open_count else "🔴 Hozir barchasi yopiq"

    lines = [f"💊 <b>{medicine_name}</b> — {total} ta dorixona\n"]

    for i, p in enumerate(pharmacies, 1):
        price      = int(p["price"])
        open_status = p.get("open_status", "")
        name       = p["name"]
        address    = p.get("address", "")
        dist       = p["distance_km"]
        phone      = p.get("phone", "")

        # Manzil: agar faqat "Toshkent" bo'lsa ko'rsatmaymiz
        addr_line = f"\n   📍 {address}" if address and address.lower() != "toshkent" else ""

        phone_line = f"\n   📞 {phone}" if phone else ""

        lines.append(
            f"{i}. <b>{name}</b>  {open_status}"
            f"{addr_line}"
            f"\n   💰 ~{price:,} so'm  |  📏 {dist} km"
            f"{phone_line}\n"
        )

    lines.append(open_label)
    lines.append("\n<i>⚠️ Narxlar taxminiy. Aniq narq uchun dorixonaga murojaat qiling.</i>")
    return "\n".join(lines)


def format_generic_alternatives(alternatives: list[dict], current_medicine: str) -> str:
    if not alternatives:
        return ""
    lines = [f"\n💡 <b>Arzon muqobil</b> ({current_medicine} o'rniga):"]
    for alt in alternatives:
        mn = alt.get("price_min", 0)
        mx = alt.get("price_max", 0)
        price_str = f"{mn:,}–{mx:,} so'm" if mn and mx else ""
        lines.append(f"   ⚡ {alt['name_uz']}" + (f" — {price_str}" if price_str else ""))
    return "\n".join(lines)
