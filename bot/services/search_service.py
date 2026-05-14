"""
Dori qidiruv pipeline:
query → NLP → DB regex → fuzzy → geo + open_now → generic muqobil → format
Agar topilmasa → alomat tekshiruvi (Claude)
"""

from __future__ import annotations
from difflib import SequenceMatcher
from loguru import logger

from bot.agents import nlp_agent, search_agent, symptom_agent
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
        text, image_url, display_name, medicine_id, found,
        generic_alternatives, is_symptom, symptom_medicines, symptom_advice
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

    # Topilmasa → alomat tekshiruvi
    if not medicines:
        symptom_result = await symptom_agent.detect_symptom(user_query)
        await queries.log_search(telegram_id, user_query, 0)

        if symptom_result.get("is_symptom") and symptom_result.get("medicines"):
            return {
                "text": "",
                "image_url": None,
                "display_name": user_query,
                "medicine_id": None,
                "found": False,
                "is_symptom": True,
                "symptom_medicines": symptom_result["medicines"],
                "symptom_advice": symptom_result.get("advice", ""),
                "generic_alternatives": [],
            }

        return {
            "text": (
                f"❓ <b>{user_query}</b> topilmadi.\n\n"
                "• To'g'ri yozilganini tekshiring\n"
                "• Generic nomini sinab ko'ring\n"
                "• <i>Paracetamol, Ibuprofen, No-shpa</i>"
            ),
            "image_url": None,
            "display_name": user_query,
            "medicine_id": None,
            "found": False,
            "is_symptom": False,
            "symptom_medicines": [],
            "symptom_advice": "",
            "generic_alternatives": [],
        }

    medicine = medicines[0]
    image_url = medicine.get("image_url")
    medicine_id = str(medicine["_id"])
    generic_name = medicine.get("generic_name", "")

    pharmacies = await queries.find_nearby_pharmacies_with_medicine(
        medicine_id=medicine["_id"],
        user_lat=user_lat,
        user_lng=user_lng,
        radius_km=settings.SEARCH_RADIUS_KM,
        limit=settings.MAX_RESULTS,
    )

    # Generic muqobillari
    alternatives = await queries.find_generic_alternatives(medicine["_id"], generic_name)

    await queries.log_search(telegram_id, user_query, len(pharmacies))
    text = await search_agent.format_results(pharmacies, display_name)

    return {
        "text": text,
        "image_url": image_url,
        "display_name": display_name,
        "medicine_id": medicine_id,
        "found": True,
        "is_symptom": False,
        "symptom_medicines": [],
        "symptom_advice": "",
        "generic_alternatives": alternatives,
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
    return [med for _, med in scored[:3]]
