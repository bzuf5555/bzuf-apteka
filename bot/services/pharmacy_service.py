"""Dorixona va dori ma'lumotlarini MongoDB ga qo'shish."""

from datetime import datetime, timezone
from bson import ObjectId
from bot.database.connection import get_db
from bot.database.models import PHARMACIES, MEDICINES, INVENTORY


async def add_pharmacy(
    name: str, address: str, lat: float, lng: float,
    phone: str = "", working_hours: str = "08:00-22:00",
) -> ObjectId:
    db = await get_db()
    doc = {
        "name": name,
        "address": address,
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "phone": phone,
        "working_hours": working_hours,
        "is_verified": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db[PHARMACIES].insert_one(doc)
    return result.inserted_id


async def add_medicine(
    name_uz: str, name_ru: str = "", generic_name: str = "",
    category: str = "", synonyms: list[str] | None = None,
) -> ObjectId:
    db = await get_db()
    doc = {
        "name_uz": name_uz,
        "name_ru": name_ru,
        "generic_name": generic_name,
        "category": category,
        "synonyms": synonyms or [],
    }
    result = await db[MEDICINES].insert_one(doc)
    return result.inserted_id


async def set_inventory(
    pharmacy_id: ObjectId, medicine_id: ObjectId,
    price: float, in_stock: bool = True,
) -> None:
    db = await get_db()
    await db[INVENTORY].update_one(
        {"pharmacy_id": pharmacy_id, "medicine_id": medicine_id},
        {
            "$set": {
                "price": price,
                "in_stock": in_stock,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )
