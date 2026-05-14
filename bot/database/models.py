"""
MongoDB kolleksiya nomlari va index ta'riflari.
migrate.py orqali indexlar yaratiladi.
"""

USERS = "users"
MEDICINES = "medicines"
PHARMACIES = "pharmacies"
INVENTORY = "inventory"
SEARCH_LOG = "search_log"
PRICE_WATCHES = "price_watches"
SAVED_MEDICINES = "saved_medicines"
REMINDERS = "reminders"
RATINGS = "ratings"


async def create_indexes(db) -> None:
    """Barcha zarur indexlarni yaratadi. Idempotent — xavfsiz qayta chaqirish mumkin."""
    from pymongo import ASCENDING, GEOSPHERE

    await db[USERS].create_index("telegram_id", unique=True)

    await db[MEDICINES].create_index([("name_uz", ASCENDING)])
    await db[MEDICINES].create_index([("name_ru", ASCENDING)])
    await db[MEDICINES].create_index([("generic_name", ASCENDING)])

    # 2dsphere — MongoDB native geo qidiruvlari uchun (ST_DWithin ekvivalenti)
    await db[PHARMACIES].create_index([("location", GEOSPHERE)])
    await db[PHARMACIES].create_index("is_active")

    await db[INVENTORY].create_index([("medicine_id", ASCENDING), ("in_stock", ASCENDING)])
    await db[INVENTORY].create_index("pharmacy_id")
    await db[INVENTORY].create_index(
        [("pharmacy_id", ASCENDING), ("medicine_id", ASCENDING)], unique=True
    )

    await db[SEARCH_LOG].create_index("telegram_id")
    await db[SEARCH_LOG].create_index("searched_at")

    await db[PRICE_WATCHES].create_index([("telegram_id", ASCENDING), ("medicine_id", ASCENDING)], unique=True)
    await db[PRICE_WATCHES].create_index("is_active")

    await db[SAVED_MEDICINES].create_index([("telegram_id", ASCENDING), ("medicine_id", ASCENDING)], unique=True)
    await db[SAVED_MEDICINES].create_index("telegram_id")

    await db[REMINDERS].create_index("telegram_id")
    await db[REMINDERS].create_index("is_active")

    await db[RATINGS].create_index([("telegram_id", ASCENDING), ("pharmacy_id", ASCENDING)], unique=True)
    await db[RATINGS].create_index("pharmacy_id")
