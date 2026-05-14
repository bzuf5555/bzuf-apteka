"""
Overpass API (OpenStreetMap) dan haqiqiy Toshkent dorixonalarini olib
MongoDB Atlas ga yozadi.

Ishlash tartibi:
1. Overpass API → Toshkent chegarasidagi barcha "amenity=pharmacy" ni oladi
2. Koordinatalar, nom, manzil, telefon, ish vaqtini oladi
3. MongoDB ga yozadi (idempotent — ikki marta ishlasa ham takrorlanmaydi)
4. Mavjud dorlar bilan inventar yaratadi
"""
import asyncio
import sys
import json
import random
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
from loguru import logger
from bot.database.connection import get_db, close_db
from bot.database.models import create_indexes, PHARMACIES, MEDICINES, INVENTORY

# Toshkent shahrining bounding box (janub, g'arb, shimol, sharq)
TASHKENT_BBOX = (41.21, 69.13, 41.40, 69.50)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:30];
(
  node["amenity"="pharmacy"]({s},{w},{n},{e});
  way["amenity"="pharmacy"]({s},{w},{n},{e});
  relation["amenity"="pharmacy"]({s},{w},{n},{e});
);
out center body;
""".format(s=TASHKENT_BBOX[0], w=TASHKENT_BBOX[1],
           n=TASHKENT_BBOX[2], e=TASHKENT_BBOX[3])


def _extract(element: dict) -> dict | None:
    """OSM elementdan kerakli ma'lumotlarni ajratib oladi."""
    tags = element.get("tags", {})

    # Koordinatalar
    if element["type"] == "node":
        lat = element.get("lat")
        lng = element.get("lon")
    else:
        center = element.get("center", {})
        lat = center.get("lat")
        lng = center.get("lon")

    if not lat or not lng:
        return None

    # Nom — o'zbekcha, ruscha yoki umumiy
    name = (
        tags.get("name:uz")
        or tags.get("name:ru")
        or tags.get("name")
        or "Dorixona"
    )

    # Manzil
    parts = []
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
    if tags.get("addr:housenumber"):
        parts.append(tags["addr:housenumber"])
    if tags.get("addr:suburb") or tags.get("addr:district"):
        parts.append(tags.get("addr:suburb") or tags["addr:district"])
    if not parts and tags.get("description"):
        parts.append(tags["description"][:80])
    address = ", ".join(parts) if parts else "Toshkent"

    # Telefon
    phone = tags.get("phone") or tags.get("contact:phone") or ""
    if phone:
        phone = phone.replace(" ", "").replace("-", "")
        if not phone.startswith("+"):
            phone = "+" + phone.lstrip("+")

    # Ish vaqti
    hours = tags.get("opening_hours", "08:00-22:00")
    if hours == "24/7":
        hours = "24/7"
    elif len(hours) > 30:
        hours = "08:00-22:00"

    return {
        "osm_id": element["id"],
        "name": name,
        "address": address,
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "phone": phone,
        "working_hours": hours,
        "is_verified": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }


async def fetch_from_overpass() -> list[dict]:
    """Overpass API dan ma'lumot oladi."""
    logger.info("Overpass API ga so'rov yuborilmoqda...")
    timeout = aiohttp.ClientTimeout(total=40)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            OVERPASS_URL,
            data={"data": OVERPASS_QUERY},
            headers={"Accept": "application/json"},
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"Overpass xato {resp.status}: {text[:200]}")
            data = await resp.json(content_type=None)

    elements = data.get("elements", [])
    logger.info(f"Overpass: {len(elements)} ta element topildi")
    return elements


async def run():
    db = await get_db()
    await create_indexes(db)

    # Mavjud dorixonalarni OSM ID bo'yicha tekshirish
    existing_ids = set()
    async for ph in db[PHARMACIES].find({"osm_id": {"$exists": True}}, {"osm_id": 1}):
        existing_ids.add(ph["osm_id"])
    logger.info(f"Mavjud OSM dorixonalar: {len(existing_ids)} ta")

    # Overpass dan olish
    elements = await fetch_from_overpass()

    # Dorlar ro'yxatini olish
    medicines = await db[MEDICINES].find({}, {"_id": 1}).to_list(200)
    med_ids = [m["_id"] for m in medicines]
    if not med_ids:
        logger.error("Dorilar yo'q! Avval seed_data.py ni ishlatish kerak.")
        return

    prices = [5_000, 8_000, 10_000, 12_000, 15_000, 18_000, 20_000, 25_000, 30_000, 35_000, 50_000]
    inserted = 0
    skipped = 0

    for el in elements:
        ph_data = _extract(el)
        if not ph_data:
            skipped += 1
            continue

        osm_id = ph_data["osm_id"]
        if osm_id in existing_ids:
            skipped += 1
            continue

        # Dorixonani qo'shish
        result = await db[PHARMACIES].insert_one(ph_data)
        ph_id = result.inserted_id

        # Tasodifiy dorilar bilan inventar
        available_meds = random.sample(med_ids, k=random.randint(5, len(med_ids)))
        inv_docs = [
            {
                "pharmacy_id": ph_id,
                "medicine_id": mid,
                "price": random.choice(prices),
                "in_stock": True,
                "updated_at": datetime.now(timezone.utc),
            }
            for mid in available_meds
        ]
        await db[INVENTORY].insert_many(inv_docs)

        existing_ids.add(osm_id)
        inserted += 1
        logger.info(f"+ {ph_data['name']} ({ph_data['address'][:40]})")

    total = await db[PHARMACIES].count_documents({})
    logger.success(
        f"Tayyor! {inserted} ta yangi dorixona qo'shildi | "
        f"{skipped} ta o'tkazildi | Jami: {total} ta"
    )
    await close_db()


if __name__ == "__main__":
    asyncio.run(run())
