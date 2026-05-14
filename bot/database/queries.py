"""
MongoDB queries — Motor (async) orqali.
Geo qidiruv: $near + 2dsphere index (MongoDB native, Haversine kerak emas).
"""

import math
from datetime import datetime, timezone
from bson import ObjectId
from loguru import logger

from .connection import get_db
from .models import USERS, MEDICINES, PHARMACIES, INVENTORY, SEARCH_LOG


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Users ──────────────────────────────────────────────────────────────────

async def upsert_user(telegram_id: int, username: str | None, full_name: str) -> None:
    db = await get_db()
    await db[USERS].update_one(
        {"telegram_id": telegram_id},
        {
            "$set": {"username": username, "full_name": full_name, "last_active": _now()},
            "$setOnInsert": {"registered_at": _now(), "phone": None, "lat": None, "lng": None},
        },
        upsert=True,
    )


async def save_user_contact(telegram_id: int, phone: str, full_name: str) -> None:
    db = await get_db()
    await db[USERS].update_one(
        {"telegram_id": telegram_id},
        {"$set": {"phone": phone, "full_name": full_name, "last_active": _now()}},
    )


async def update_user_location(telegram_id: int, lat: float, lng: float) -> None:
    db = await get_db()
    await db[USERS].update_one(
        {"telegram_id": telegram_id},
        {"$set": {"lat": lat, "lng": lng, "last_active": _now()}},
    )


async def get_user(telegram_id: int) -> dict | None:
    db = await get_db()
    return await db[USERS].find_one({"telegram_id": telegram_id}, {"_id": 0})


async def user_has_contact(telegram_id: int) -> bool:
    user = await get_user(telegram_id)
    return bool(user and user.get("phone"))


async def user_has_location(telegram_id: int) -> bool:
    user = await get_user(telegram_id)
    return bool(user and user.get("lat") and user.get("lng"))


# ── Medicines ──────────────────────────────────────────────────────────────

async def search_medicines_by_name(query: str) -> list[dict]:
    if not query:
        return []
    db = await get_db()
    regex = {"$regex": query, "$options": "i"}
    cursor = db[MEDICINES].find(
        {"$or": [
            {"name_uz": regex},
            {"name_ru": regex},
            {"generic_name": regex},
            {"synonyms": regex},
        ]},
        {"_id": 1, "name_uz": 1, "name_ru": 1, "generic_name": 1, "category": 1, "image_url": 1},
    ).limit(10)
    return await cursor.to_list(10)


async def get_medicine_by_id(medicine_id) -> dict | None:
    db = await get_db()
    return await db[MEDICINES].find_one({"_id": medicine_id}, {"_id": 0, "name_uz": 1, "name_ru": 1})


async def find_generic_alternatives(medicine_id, generic_name: str) -> list[dict]:
    """Bir xil generic_name ga ega, arzonroq muqobillarni topadi."""
    if not generic_name:
        return []
    from pymongo import ASCENDING
    db = await get_db()
    cursor = db[MEDICINES].find(
        {"generic_name": generic_name, "_id": {"$ne": medicine_id}},
        {"_id": 1, "name_uz": 1, "price_min": 1, "price_max": 1},
    ).sort("price_min", ASCENDING).limit(3)
    return await cursor.to_list(3)


# ── Pharmacies + Geo ───────────────────────────────────────────────────────

async def find_nearby_pharmacies_with_medicine(
    medicine_id: ObjectId,
    user_lat: float,
    user_lng: float,
    radius_km: float = 5.0,
    limit: int = 10,
) -> list[dict]:
    """
    MongoDB $near (2dsphere) + inventory join.
    $near avtomatik masofaga qarab tartiblaydi.
    """
    db = await get_db()

    inv_cursor = db[INVENTORY].find(
        {"medicine_id": medicine_id, "in_stock": True},
        {"pharmacy_id": 1, "price": 1, "_id": 0},
    )
    inv_list = await inv_cursor.to_list(200)

    if not inv_list:
        return []

    pharmacy_ids = [doc["pharmacy_id"] for doc in inv_list]
    price_map = {doc["pharmacy_id"]: doc["price"] for doc in inv_list}

    # $near — 2dsphere index ishlatadi, masofa bo'yicha tartiblanadi
    nearby_cursor = db[PHARMACIES].find(
        {
            "_id": {"$in": pharmacy_ids},
            "is_active": True,
            "location": {
                "$near": {
                    "$geometry": {"type": "Point", "coordinates": [user_lng, user_lat]},
                    "$maxDistance": int(radius_km * 1000),
                }
            },
        },
        {"_id": 1, "name": 1, "address": 1, "location": 1, "phone": 1, "working_hours": 1},
    ).limit(limit)

    from bot.services.geo_service import is_open_now

    results = []
    for ph in await nearby_cursor.to_list(limit):
        coords = ph["location"]["coordinates"]
        dist = _haversine(user_lat, user_lng, coords[1], coords[0])
        wh = ph.get("working_hours", "")
        is_open, open_status = is_open_now(wh)
        results.append({
            "id": str(ph["_id"]),
            "name": ph["name"],
            "address": ph["address"],
            "lat": coords[1],
            "lng": coords[0],
            "phone": ph.get("phone", ""),
            "working_hours": wh,
            "open_status": open_status,
            "is_open": is_open,
            "price": price_map.get(ph["_id"], 0),
            "distance_km": round(dist, 2),
        })

    # Ochiq dorixonalar birinchi
    results.sort(key=lambda x: (not x["is_open"], x["distance_km"]))
    return results


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


# ── Search Log ─────────────────────────────────────────────────────────────

async def log_search(telegram_id: int, query: str, results_count: int) -> None:
    db = await get_db()
    await db[SEARCH_LOG].insert_one({
        "telegram_id": telegram_id,
        "query": query,
        "results_count": results_count,
        "searched_at": _now(),
    })


# ── Price Watches ──────────────────────────────────────────────────────────

async def subscribe_price_watch(
    telegram_id: int,
    medicine_id,
    medicine_name: str,
    user_lat: float,
    user_lng: float,
    current_min_price: float,
) -> bool:
    """
    Foydalanuvchini dori narqi kuzatuviga qo'shadi.
    Returns: True — yangi, False — allaqachon obuna
    """
    from .models import PRICE_WATCHES
    db = await get_db()
    existing = await db[PRICE_WATCHES].find_one({
        "telegram_id": telegram_id,
        "medicine_id": medicine_id,
    })
    if existing:
        if not existing.get("is_active"):
            await db[PRICE_WATCHES].update_one(
                {"_id": existing["_id"]},
                {"$set": {"is_active": True, "min_price": current_min_price, "updated_at": _now()}},
            )
            return True
        return False

    await db[PRICE_WATCHES].insert_one({
        "telegram_id": telegram_id,
        "medicine_id": medicine_id,
        "medicine_name": medicine_name,
        "user_lat": user_lat,
        "user_lng": user_lng,
        "min_price": current_min_price,
        "subscribed_at": _now(),
        "last_checked_at": _now(),
        "is_active": True,
    })
    return True


async def unsubscribe_price_watch(telegram_id: int, medicine_id) -> None:
    from .models import PRICE_WATCHES
    db = await get_db()
    await db[PRICE_WATCHES].update_one(
        {"telegram_id": telegram_id, "medicine_id": medicine_id},
        {"$set": {"is_active": False}},
    )


async def get_active_watches() -> list[dict]:
    from .models import PRICE_WATCHES
    db = await get_db()
    cursor = db[PRICE_WATCHES].find({"is_active": True})
    return await cursor.to_list(None)


async def update_watch_price(watch_id, new_min_price: float) -> None:
    from .models import PRICE_WATCHES
    db = await get_db()
    await db[PRICE_WATCHES].update_one(
        {"_id": watch_id},
        {"$set": {"min_price": new_min_price, "last_checked_at": _now()}},
    )


async def get_current_min_price(medicine_id, user_lat: float, user_lng: float, radius_km: float = 5.0) -> float | None:
    """Foydalanuvchi atrofida dorining eng arzon narxini qaytaradi."""
    pharmacies = await find_nearby_pharmacies_with_medicine(
        medicine_id=medicine_id,
        user_lat=user_lat,
        user_lng=user_lng,
        radius_km=radius_km,
    )
    if not pharmacies:
        return None
    return min(p["price"] for p in pharmacies)


# ── Saved Medicines ────────────────────────────────────────────────────────

async def save_medicine(telegram_id: int, medicine_id, medicine_name: str) -> bool:
    from .models import SAVED_MEDICINES
    db = await get_db()
    try:
        await db[SAVED_MEDICINES].update_one(
            {"telegram_id": telegram_id, "medicine_id": medicine_id},
            {"$setOnInsert": {"medicine_name": medicine_name, "saved_at": _now()}},
            upsert=True,
        )
        return True
    except Exception:
        return False


async def remove_saved_medicine(telegram_id: int, medicine_id) -> None:
    from .models import SAVED_MEDICINES
    db = await get_db()
    await db[SAVED_MEDICINES].delete_one({"telegram_id": telegram_id, "medicine_id": medicine_id})


async def get_saved_medicines(telegram_id: int) -> list[dict]:
    from .models import SAVED_MEDICINES
    db = await get_db()
    cursor = db[SAVED_MEDICINES].find(
        {"telegram_id": telegram_id},
        {"medicine_id": 1, "medicine_name": 1, "_id": 0},
    ).sort("saved_at", -1).limit(20)
    return await cursor.to_list(20)


async def is_medicine_saved(telegram_id: int, medicine_id) -> bool:
    from .models import SAVED_MEDICINES
    db = await get_db()
    doc = await db[SAVED_MEDICINES].find_one({"telegram_id": telegram_id, "medicine_id": medicine_id})
    return bool(doc)


# ── Reminders ──────────────────────────────────────────────────────────────

async def create_reminder(telegram_id: int, medicine_name: str, times: list[str]) -> None:
    from .models import REMINDERS
    db = await get_db()
    await db[REMINDERS].insert_one({
        "telegram_id": telegram_id,
        "medicine_name": medicine_name,
        "times": times,
        "is_active": True,
        "created_at": _now(),
    })


async def get_user_reminders(telegram_id: int) -> list[dict]:
    from .models import REMINDERS
    db = await get_db()
    cursor = db[REMINDERS].find(
        {"telegram_id": telegram_id, "is_active": True},
        {"_id": 1, "medicine_name": 1, "times": 1},
    )
    return await cursor.to_list(10)


async def delete_reminder(reminder_id) -> None:
    from .models import REMINDERS
    db = await get_db()
    await db[REMINDERS].update_one({"_id": reminder_id}, {"$set": {"is_active": False}})


async def get_active_reminders() -> list[dict]:
    from .models import REMINDERS
    db = await get_db()
    cursor = db[REMINDERS].find({"is_active": True})
    return await cursor.to_list(None)


# ── Ratings ────────────────────────────────────────────────────────────────

async def save_rating(telegram_id: int, pharmacy_id_str: str, rating: int, comment: str = "") -> None:
    from .models import RATINGS
    from bson import ObjectId
    db = await get_db()
    try:
        ph_id = ObjectId(pharmacy_id_str)
    except Exception:
        return
    await db[RATINGS].update_one(
        {"telegram_id": telegram_id, "pharmacy_id": ph_id},
        {"$set": {"rating": rating, "comment": comment, "rated_at": _now()}},
        upsert=True,
    )


async def get_pharmacy_avg_rating(pharmacy_id_str: str) -> tuple[float, int]:
    """(o'rtacha reyting, baholashlar soni)"""
    from .models import RATINGS
    from bson import ObjectId
    try:
        ph_id = ObjectId(pharmacy_id_str)
    except Exception:
        return 0.0, 0
    db = await get_db()
    pipeline = [
        {"$match": {"pharmacy_id": ph_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    result = await db[RATINGS].aggregate(pipeline).to_list(1)
    if result:
        return round(result[0]["avg"], 1), result[0]["count"]
    return 0.0, 0


# ── Search History ─────────────────────────────────────────────────────────

async def get_search_history(telegram_id: int, limit: int = 10) -> list[dict]:
    db = await get_db()
    cursor = db[SEARCH_LOG].find(
        {"telegram_id": telegram_id, "results_count": {"$gt": 0}},
        {"query": 1, "results_count": 1, "searched_at": 1, "_id": 0},
    ).sort("searched_at", -1).limit(limit)
    return await cursor.to_list(limit)


# ── Admin stats ────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    db = await get_db()
    return {
        label: await db[col].count_documents({})
        for col, label in [
            (USERS, "users"),
            (PHARMACIES, "pharmacies"),
            (MEDICINES, "medicines"),
            (INVENTORY, "inventory"),
            (SEARCH_LOG, "searches"),
        ]
    }
