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

    results = []
    for ph in await nearby_cursor.to_list(limit):
        coords = ph["location"]["coordinates"]
        dist = _haversine(user_lat, user_lng, coords[1], coords[0])
        results.append({
            "id": str(ph["_id"]),
            "name": ph["name"],
            "address": ph["address"],
            "lat": coords[1],
            "lng": coords[0],
            "phone": ph.get("phone", ""),
            "working_hours": ph.get("working_hours", ""),
            "price": price_map.get(ph["_id"], 0),
            "distance_km": round(dist, 2),
        })

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
