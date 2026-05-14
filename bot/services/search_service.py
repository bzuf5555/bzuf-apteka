"""
6 bosqichli dori qidiruv pipeline:

1. Original so'rov → DB regex (tez, aniq)
2. NLP normalize → DB regex (imlo xatolari uchun)
3. Fuzzy match — TUZATILDI (endi ishlaydi)
4. Har bir so'z alohida — "No-Shpa 40mg" → "No-Shpa" + "40mg"
5. Brand→Generic (Claude) → DB regex — yangi!
6. Alomat tekshiruvi — faqat haqiqiy alomat uchun

Agar barchasi muvaffaqiyatsiz → eng yaqin o'xshashlarni ko'rsatish
"""

from __future__ import annotations
from difflib import SequenceMatcher
from loguru import logger

from bot.agents import nlp_agent, search_agent, symptom_agent, brand_agent
from bot.database import queries
from bot.config import settings

# Dorimiga o'xshash so'zlar (alomat agentini noto'g'ri ishga tushirmaslik uchun)
_SYMPTOM_KEYWORDS = {
    "og'riyapti", "og'riq", "harorat", "isitma", "yo'tal", "tumov",
    "ich", "qornim", "boshim", "ko'nglim", "qusmoqchi", "uyqusizlik",
    "qichishadi", "qizargan", "shishgan", "bolam", "farzandim",
    "болит", "температура", "кашель", "насморк", "тошнит", "понос",
}


def _looks_like_symptom(query: str) -> bool:
    """Foydalanuvchi kiritmasini alomat deb taxmin qilish."""
    words = query.lower().split()
    # Ko'p so'zli va alomat kalit so'zlari bor bo'lsa
    return len(words) >= 3 and any(w in _SYMPTOM_KEYWORDS for w in words)


async def _db_search(terms: list[str]) -> list[dict]:
    """Berilgan terminlar bo'yicha DB dan qidiradi."""
    for term in terms:
        if not term or len(term) < 2:
            continue
        results = await queries.search_medicines_by_name(term)
        if results:
            return results
    return []


async def _fuzzy_search_fixed(query: str) -> list[dict]:
    """
    To'g'rilangan fuzzy qidiruv.
    TUZATISH: avval search_medicines_by_name("") ishlatilgan —
    bu har doim [] qaytarardi. Endi get_all_medicines_list() ishlatiladi.
    """
    all_meds = await queries.get_all_medicines_list()
    if not all_meds:
        return []

    q = query.lower().strip()
    scored = []
    for med in all_meds:
        # name_uz, name_ru, generic_name va synonyms bilan solishtirish
        candidates = [
            med.get("name_uz", "").lower(),
            med.get("name_ru", "").lower(),
            med.get("generic_name", "").lower(),
        ]
        synonyms = med.get("synonyms") or []
        if isinstance(synonyms, list):
            candidates.extend([s.lower() for s in synonyms])

        score = max(
            (SequenceMatcher(None, q, c).ratio() for c in candidates if c),
            default=0,
        )
        if score >= 0.55:  # Avval 0.65 edi — ko'proq natija uchun pasaytirdik
            scored.append((score, med))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [med for _, med in scored[:3]]


async def _suggest_closest(query: str) -> str:
    """DB da topilmagan dori uchun eng yaqin o'xshashlarni taklif qiladi."""
    all_meds = await queries.get_all_medicines_list()
    if not all_meds:
        return ""

    q = query.lower()
    scored = [
        (SequenceMatcher(None, q, med.get("name_uz", "").lower()).ratio(), med)
        for med in all_meds
    ]
    scored.sort(reverse=True)
    top = [m["name_uz"] for _, m in scored[:3] if _ > 0.3]

    if top:
        suggestions = "\n".join(f"   • <i>{n}</i>" for n in top)
        return f"\n\n💡 Ehtimol siz qidirayotgan dori:\n{suggestions}"
    return ""


async def search_medicine(
    user_query: str,
    user_lat: float,
    user_lng: float,
    telegram_id: int,
) -> dict:
    logger.info(f"Qidiruv: '{user_query}' ({user_lat:.4f}, {user_lng:.4f})")
    q = user_query.strip()

    # ── 1. Original so'rov → DB (tez yo'l) ───────────────────────────────────
    medicines = await _db_search([q])

    # ── 2. NLP normalize → DB ─────────────────────────────────────────────────
    if not medicines:
        normalized = await nlp_agent.normalize_medicine_name(q)
        search_terms = normalized.get("search_terms", [])
        display_hint = normalized.get("generic_name")
        medicines = await _db_search(search_terms)
    else:
        normalized = {}
        display_hint = None

    # ── 3. Fuzzy match (TUZATILDI) ────────────────────────────────────────────
    if not medicines:
        medicines = await _fuzzy_search_fixed(q)

    # ── 4. Har bir so'z alohida ("No-Shpa 40mg" → "No-Shpa") ─────────────────
    if not medicines:
        words = [w for w in q.split() if len(w) >= 3]
        medicines = await _db_search(words)

    # ── 5. Brand → Generic (Claude) → DB ─────────────────────────────────────
    if not medicines:
        brand_result = await brand_agent.get_generic_name(q)
        if brand_result.get("is_medicine") and brand_result.get("generic"):
            generic = brand_result["generic"]
            medicines = await _db_search([generic, generic.split()[0]])

    # ── 6. Alomat tekshiruvi (faqat haqiqiy alomat uchun) ─────────────────────
    if not medicines:
        is_probable_symptom = _looks_like_symptom(q)

        if is_probable_symptom:
            symptom_result = await symptom_agent.detect_symptom(q)
            await queries.log_search(telegram_id, q, 0)
            if symptom_result.get("is_symptom") and symptom_result.get("medicines"):
                return {
                    "text": "",
                    "image_url": None,
                    "display_name": q,
                    "medicine_id": None,
                    "found": False,
                    "is_symptom": True,
                    "symptom_medicines": symptom_result["medicines"],
                    "symptom_advice": symptom_result.get("advice", ""),
                    "generic_alternatives": [],
                }

        # Haqiqatan topilmadi
        suggestions = await _suggest_closest(q)
        await queries.log_search(telegram_id, q, 0)
        return {
            "text": (
                f"❓ <b>{q}</b> bizning ro'yxatimizda topilmadi.{suggestions}\n\n"
                "Boshqacha yozib ko'ring yoki generic nomini ishlating.\n"
                "<i>Masalan: Paracetamol, Ibuprofen, Drotaverine</i>"
            ),
            "image_url": None,
            "display_name": q,
            "medicine_id": None,
            "found": False,
            "is_symptom": False,
            "symptom_medicines": [],
            "symptom_advice": "",
            "generic_alternatives": [],
        }

    # ── Natija topildi ────────────────────────────────────────────────────────
    medicine = medicines[0]
    display_name = display_hint or medicine.get("name_uz", q)
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

    alternatives = await queries.find_generic_alternatives(medicine["_id"], generic_name)
    await queries.log_search(telegram_id, q, len(pharmacies))
    text = await search_agent.format_results(pharmacies, display_name)

    return {
        "text": text,
        "image_url": image_url,
        "display_name": display_name,
        "medicine_id": medicine_id,
        "pharmacies": pharmacies,          # ← lokatsiya tugmalari uchun
        "found": True,
        "is_symptom": False,
        "symptom_medicines": [],
        "symptom_advice": "",
        "generic_alternatives": alternatives,
    }
