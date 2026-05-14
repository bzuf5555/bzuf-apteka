"""
Dori qidiruv pipeline:
user query → NLP normalize → MongoDB regex + fuzzy → geo filter ($near) → format
Returns: {"text": str, "image_url": str|None, "display_name": str}
"""

from __future__ import annotations
from difflib import SequenceMatcher
from loguru import logger

from bot.agents import nlp_agent, search_agent
from bot.database import queries
from bot.config import settings


async def search_medicine(
    user_query: str,
    user_lat: float,
    user_lng: float,
    telegram_id: int,
) -> dict:
    """
    Returns:
        {
            "text": str,        - HTML formatted result
            "image_url": str|None,
            "display_name": str,
            "found": bool
        }
    """
    logger.info(f"Qidiruv: '{user_query}' ({user_lat:.4f}, {user_lng:.4f})")

    normalized = await nlp_agent.normalize_medicine_name(user_query)
    search_terms = normalized.get("search_terms", [user_query.lower()])
    display_name = normalized.get("generic_name") or user_query

    medicines = []
    for term in search_terms:
        medicines = await queries.search_medicines_by_name(term)
        if medicines:
            break

    if not medicines:
        medicines = await _fuzzy_search(user_query)

    if not medicines:
        await queries.log_search(telegram_id, user_query, 0)
        return {
            "text": (
                f"❓ <b>{user_query}</b> dori topilmadi.\n\n"
                "Iltimos:\n"
                "• To'g'ri yozilganini tekshiring\n"
                "• Generic nomini sinab ko'ring\n"
                "• Masalan: <i>Paracetamol, Ibuprofen, Amoxicillin</i>"
            ),
            "image_url": None,
            "display_name": user_query,
            "found": False,
        }

    medicine = medicines[0]
    image_url = medicine.get("image_url")

    pharmacies = await queries.find_nearby_pharmacies_with_medicine(
        medicine_id=medicine["_id"],
        user_lat=user_lat,
        user_lng=user_lng,
        radius_km=settings.SEARCH_RADIUS_KM,
        limit=settings.MAX_RESULTS,
    )

    await queries.log_search(telegram_id, user_query, len(pharmacies))
    text = await search_agent.format_results(pharmacies, display_name)

    return {
        "text": text,
        "image_url": image_url,
        "display_name": display_name,
        "found": True,
    }


async def _fuzzy_search(query: str) -> list[dict]:
    all_meds = await queries.search_medicines_by_name("")
    if not all_meds:
        return []
    q = query.lower()
    scored = []
    for med in all_meds:
        score = max(
            SequenceMatcher(None, q, med["name_uz"].lower()).ratio(),
            SequenceMatcher(None, q, (med.get("generic_name") or "").lower()).ratio(),
        )
        if score >= 0.65:
            scored.append((score, med))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = [med for _, med in scored[:3]]
    logger.debug(f"Fuzzy: '{query}' → {len(results)} natija")
    return results
