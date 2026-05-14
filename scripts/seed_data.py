"""
Demo ma'lumot: 10 Toshkent dorixonasi + 15 dori + inventar.
Idempotent — qayta ishlasa ham takrorlanmaydi.
"""
import asyncio
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.database.connection import get_db, close_db
from bot.database.models import create_indexes, PHARMACIES, MEDICINES
from bot.services.pharmacy_service import add_pharmacy, add_medicine, set_inventory
from loguru import logger

PHARMACIES_DATA = [
    {"name": "Farzona Apteka",      "address": "Yunusobod, 10-kvartal, 12-uy",       "lat": 41.3368, "lng": 69.3481, "phone": "+998712345678", "hours": "08:00-22:00"},
    {"name": "Shifobaxsh Dorixona", "address": "Chilonzor, 9-kvartal, 5-uy",         "lat": 41.2846, "lng": 69.2068, "phone": "+998712345679", "hours": "09:00-21:00"},
    {"name": "Mega Apteka",         "address": "Mirzo Ulug'bek, Olmazar bozori",      "lat": 41.3156, "lng": 69.3207, "phone": "+998712345680", "hours": "08:00-23:00"},
    {"name": "Al-Shifa",            "address": "Shayxontohur, Navoiy ko'chasi, 3",    "lat": 41.3005, "lng": 69.2742, "phone": "+998712345681", "hours": "24/7"},
    {"name": "Dori Darmon",         "address": "Uchtepa, Qoratosh bozori",            "lat": 41.2938, "lng": 69.2321, "phone": "+998712345682", "hours": "08:00-20:00"},
    {"name": "Salomatlik Apteka",   "address": "Sergeli, 14-kvartal",                 "lat": 41.2324, "lng": 69.2712, "phone": "+998712345683", "hours": "08:00-22:00"},
    {"name": "Hayot Dorixona",      "address": "Bektemir, Yangi hayot ko'chasi",      "lat": 41.2712, "lng": 69.3845, "phone": "+998712345684", "hours": "09:00-21:00"},
    {"name": "Baraka Apteka",       "address": "Yakkasaray, Amir Temur shoh k., 108", "lat": 41.2987, "lng": 69.2654, "phone": "+998712345685", "hours": "08:00-22:00"},
    {"name": "Nur Dorixona",        "address": "Olmazor, Dustlik ko'chasi, 22",       "lat": 41.3421, "lng": 69.2987, "phone": "+998712345686", "hours": "09:00-20:00"},
    {"name": "Shifa Plus",          "address": "Mirobod, Shota Rustaveli k., 16",     "lat": 41.3089, "lng": 69.2845, "phone": "+998712345687", "hours": "08:00-23:00"},
]

MEDICINES_DATA = [
    {"name_uz": "Paracetamol",             "name_ru": "Парацетамол",     "generic_name": "paracetamol",         "category": "Analgetik",       "synonyms": ["acetaminophen", "paratsetamol", "tylenol"]},
    {"name_uz": "Ibuprofen",               "name_ru": "Ибупрофен",       "generic_name": "ibuprofen",           "category": "NSAID",           "synonyms": ["ibufen", "nurofen", "ibuprofin"]},
    {"name_uz": "Amoxicillin",             "name_ru": "Амоксициллин",    "generic_name": "amoxicillin",         "category": "Antibiotik",      "synonyms": ["amoksitsillin", "flemoxin", "ospamox"]},
    {"name_uz": "Aspirin",                 "name_ru": "Аспирин",         "generic_name": "acetylsalicylic acid","category": "Analgetik",       "synonyms": ["atsetilsalisin"]},
    {"name_uz": "Ciprofloxacin",           "name_ru": "Ципрофлоксацин", "generic_name": "ciprofloxacin",       "category": "Antibiotik",      "synonyms": ["tsiprofloksatsin", "cipro"]},
    {"name_uz": "Metronidazol",            "name_ru": "Метронидазол",    "generic_name": "metronidazole",       "category": "Antibiotik",      "synonyms": ["flagyl", "metrogil"]},
    {"name_uz": "Omeprazol",               "name_ru": "Омепразол",       "generic_name": "omeprazole",          "category": "Oshqozon dori",   "synonyms": ["losek", "omez"]},
    {"name_uz": "Loratadin",               "name_ru": "Лоратадин",       "generic_name": "loratadine",          "category": "Antigistamin",    "synonyms": ["claritin", "loridin"]},
    {"name_uz": "No-shpa",                 "name_ru": "Но-шпа",          "generic_name": "drotaverine",         "category": "Spazmolitik",     "synonyms": ["drotaverin", "noshpa"]},
    {"name_uz": "Validol",                 "name_ru": "Валидол",         "generic_name": "validol",             "category": "Yurak dori",      "synonyms": ["validola"]},
    {"name_uz": "Bisoprolol",              "name_ru": "Бисопролол",      "generic_name": "bisoprolol",          "category": "Beta-bloker",     "synonyms": ["concor", "bisoprolo"]},
    {"name_uz": "Enalapril",               "name_ru": "Эналаприл",       "generic_name": "enalapril",           "category": "Gipertoniya",     "synonyms": ["enap", "enam"]},
    {"name_uz": "Vitamin C",               "name_ru": "Витамин С",       "generic_name": "ascorbic acid",       "category": "Vitamin",         "synonyms": ["askorbin kislota", "askorbinka"]},
    {"name_uz": "Metformin (Glucophage)",  "name_ru": "Глюкофаж",        "generic_name": "metformin",           "category": "Diabet dori",     "synonyms": ["metformin", "siofor"]},
    {"name_uz": "Diazepam",               "name_ru": "Диазепам",         "generic_name": "diazepam",            "category": "Tinchlantiruvchi","synonyms": ["valium", "relanium"]},
]


async def seed() -> None:
    db = await get_db()
    await create_indexes(db)

    ph_exists = await db[PHARMACIES].count_documents({})
    med_exists = await db[MEDICINES].count_documents({})

    if ph_exists > 0 or med_exists > 0:
        logger.warning(f"Ma'lumot allaqachon mavjud: {ph_exists} dorixona, {med_exists} dori. O'tkazib yuborildi.")
        await close_db()
        return

    ph_ids = []
    for ph in PHARMACIES_DATA:
        pid = await add_pharmacy(
            name=ph["name"], address=ph["address"],
            lat=ph["lat"], lng=ph["lng"],
            phone=ph["phone"], working_hours=ph["hours"],
        )
        ph_ids.append(pid)
        logger.info(f"+ Dorixona: {ph['name']}")

    med_ids = []
    for med in MEDICINES_DATA:
        mid = await add_medicine(**med)
        med_ids.append(mid)
        logger.info(f"+ Dori: {med['name_uz']}")

    random.seed(42)
    prices = [5_000, 8_000, 12_000, 15_000, 20_000, 25_000, 35_000, 50_000]
    inv_count = 0
    for ph_id in ph_ids:
        available = random.sample(med_ids, k=random.randint(6, len(med_ids)))
        for med_id in available:
            await set_inventory(ph_id, med_id, random.choice(prices), in_stock=True)
            inv_count += 1

    logger.success(f"Seed tayyor! {len(ph_ids)} dorixona | {len(med_ids)} dori | {inv_count} inventar")
    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
