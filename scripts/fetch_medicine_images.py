"""
Wikipedia REST API dan har bir dori uchun rasm URL oladi.
URL MongoDB da medicines.image_url ga saqlanadi.

Wikipedia har bir dori uchun yuqori sifatli, Creative Commons
litsenziyasi ostidagi rasmlarni bepul taqdim etadi.
"""
import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent.parent))

import aiohttp
from loguru import logger
from bot.database.connection import get_db, close_db
from bot.database.models import MEDICINES

# Wikipedia API
WP_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
WP_SEARCH  = "https://en.wikipedia.org/w/api.php"

# Generik nomlar → Wikipedia maqola nomi (agar farq qilsa)
WIKI_OVERRIDES: dict[str, str] = {
    "paracetamol":               "Paracetamol",
    "ibuprofen":                 "Ibuprofen",
    "acetylsalicylic acid":      "Aspirin",
    "paracetamol+caffeine":      "Paracetamol",
    "drotaverine":               "Drotaverine",
    "papaverine":                "Papaverine",
    "hyoscine":                  "Hyoscine",
    "metamizole sodium":         "Metamizole",
    "ketorolac":                 "Ketorolac",
    "nimesulide":                "Nimesulide",
    "diclofenac":                "Diclofenac",
    "amoxicillin":               "Amoxicillin",
    "amoxicillin+clavulanate":   "Co-amoxiclav",
    "azithromycin":              "Azithromycin",
    "ciprofloxacin":             "Ciprofloxacin",
    "levofloxacin":              "Levofloxacin",
    "metronidazole":             "Metronidazole",
    "doxycycline":               "Doxycycline",
    "clindamycin":               "Clindamycin",
    "ceftriaxone":               "Ceftriaxone",
    "fluconazole":               "Fluconazole",
    "bisoprolol":                "Bisoprolol",
    "amlodipine":                "Amlodipine",
    "enalapril":                 "Enalapril",
    "lisinopril":                "Lisinopril",
    "losartan":                  "Losartan",
    "atorvastatin":              "Atorvastatin",
    "rosuvastatin":              "Rosuvastatin",
    "validol":                   "Menthol",
    "nitroglycerin":             "Nitroglycerin",
    "warfarin":                  "Warfarin",
    "clopidogrel":               "Clopidogrel",
    "digoxin":                   "Digoxin",
    "omeprazole":                "Omeprazole",
    "pantoprazole":              "Pantoprazole",
    "esomeprazole":              "Esomeprazole",
    "famotidine":                "Famotidine",
    "pancreatin":                "Pancreatin",
    "probiotic":                 "Probiotic",
    "loperamide":                "Loperamide",
    "diosmectite":               "Diosmectite",
    "polymethylsiloxane polyhydrate": "Activated charcoal",
    "activated charcoal":        "Activated charcoal",
    "bisacodyl":                 "Bisacodyl",
    "lactulose":                 "Lactulose",
    "domperidone":               "Domperidone",
    "metoclopramide":            "Metoclopramide",
    "loratadine":                "Loratadine",
    "cetirizine":                "Cetirizine",
    "desloratadine":             "Desloratadine",
    "chloropyramine":            "Chloropyramine",
    "dimethindene":              "Dimetindene",
    "ambroxol":                  "Ambroxol",
    "acetylcysteine":            "Acetylcysteine",
    "bromhexine":                "Bromhexine",
    "fenspiride":                "Fenspiride",
    "butamirate":                "Butamirate",
    "naphazoline":               "Naphazoline",
    "xylometazoline":            "Xylometazoline",
    "mometasone":                "Mometasone",
    "ascorbic acid":             "Vitamin C",
    "cholecalciferol":           "Cholecalciferol",
    "magnesium+pyridoxine":      "Magnesium",
    "calcium+vitamin D3":        "Calcium",
    "multivitamin":              "Multivitamin",
    "omega-3":                   "Omega-3 fatty acid",
    "folic acid":                "Folic acid",
    "iron":                      "Iron supplement",
    "zinc":                      "Zinc",
    "tocopherol":                "Tocopherol",
    "metformin":                 "Metformin",
    "glibenclamide":             "Glibenclamide",
    "gliclazide":                "Gliclazide",
    "potassium iodide":          "Potassium iodide",
    "levothyroxine":             "Levothyroxine",
    "glycine":                   "Glycine",
    "piracetam":                 "Piracetam",
    "phenibut":                  "Phenibut",
    "fabomotizole":              "Fabomotizole",
    "tofisopam":                 "Tofisopam",
    "diazepam":                  "Diazepam",
    "doxylamine":                "Doxylamine",
    "melatonin":                 "Melatonin",
    "chloramphenicol+methyluracil": "Chloramphenicol",
    "neomycin+bacitracin":       "Neomycin",
    "deproteinized hemodialysate": "Actovegin",
    "clotrimazole":              "Clotrimazole",
    "betamethasone+gentamicin+clotrimazole": "Betamethasone",
    "povidone-iodine":           "Povidone-iodine",
    "hydrogen peroxide":         "Hydrogen peroxide",
    "brilliant green":           "Brilliant green",
    "iodine":                    "Iodine",
    "chlorhexidine":             "Chlorhexidine",
    "miramistin":                "Miramistin",
    "sulfacetamide":             "Sulfacetamide",
    "tobramycin":                "Tobramycin",
    "tetryzoline":               "Tetryzoline",
    "carboxymethylcellulose":    "Carboxymethyl cellulose",
    "aciclovir":                 "Aciclovir",
    "umifenovir":                "Umifenovir",
    "glucosamine+chondroitin":   "Glucosamine",
    "ketoprofen":                "Ketoprofen",
    "drospirenone+ethinylestradiol": "Drospirenone",
    "desogestrel+ethinylestradiol": "Desogestrel",
    "levonorgestrel":            "Levonorgestrel",
    "tamsulosin":                "Tamsulosin",
    "dexamethasone":             "Dexamethasone",
    "prednisolone":              "Prednisolone",
    "levocetirizine":            "Levocetirizine",
    "nifuroxazide":              "Nifuroxazide",
    "indapamide":                "Indapamide",
    "furosemide":                "Furosemide",
    "spironolactone":            "Spironolactone",
    "framycetin":                "Framycetin",
    "amlodipine+valsartan":      "Amlodipine",
}

HEADERS = {
    "User-Agent": "DorixonaBot/1.0 (Uzbekistan pharmacy search; bzuf5555@gmail.com)"
}


async def get_wiki_image(session: aiohttp.ClientSession, generic_name: str) -> str | None:
    """Wikipedia REST API dan rasm URL oladi."""
    wiki_title = WIKI_OVERRIDES.get(generic_name.lower(), generic_name)

    # 1-urinish: REST summary endpoint
    try:
        url = WP_SUMMARY.format(quote(wiki_title.replace(" ", "_")))
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                thumb = data.get("thumbnail", {})
                if thumb and thumb.get("source"):
                    img = thumb["source"]
                    # Yuqori sifat uchun kichik o'lchamni kattaroqqa almashtirish
                    for small in ["/100px-", "/150px-", "/200px-", "/220px-", "/320px-"]:
                        img = img.replace(small, "/500px-")
                    return img
    except Exception:
        pass

    # 2-urinish: MediaWiki search API
    try:
        params = {
            "action": "query",
            "prop": "pageimages",
            "titles": wiki_title,
            "pithumbsize": 500,
            "format": "json",
            "redirects": 1,
        }
        async with session.get(WP_SEARCH, params=params, headers=HEADERS,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                pages = data.get("query", {}).get("pages", {})
                for page in pages.values():
                    thumb = page.get("thumbnail", {})
                    if thumb and thumb.get("source"):
                        return thumb["source"]
    except Exception:
        pass

    return None


async def run():
    db = await get_db()

    # Rasmi yo'q yoki null bo'lgan dorilarni olish
    cursor = db[MEDICINES].find(
        {"image_url": {"$exists": False}},
        {"_id": 1, "generic_name": 1, "name_uz": 1, "name_ru": 1}
    )
    medicines = await cursor.to_list(None)
    logger.info(f"{len(medicines)} ta dori uchun rasm qidirilmoqda...")

    found = 0
    not_found = 0

    timeout = aiohttp.ClientTimeout(total=15)
    connector = aiohttp.TCPConnector(limit=5)  # Parallel so'rovlar soni

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Sem bilan parallellik: tez lekin Wikipedia ni zo'riqtirmaymiz
        sem = asyncio.Semaphore(3)

        async def process_one(med: dict):
            nonlocal found, not_found
            async with sem:
                generic = med.get("generic_name", "")
                img_url = await get_wiki_image(session, generic)

                if img_url:
                    await db[MEDICINES].update_one(
                        {"_id": med["_id"]},
                        {"$set": {"image_url": img_url}}
                    )
                    found += 1
                    logger.info(f"✓ {med['name_uz'][:35]}")
                else:
                    await db[MEDICINES].update_one(
                        {"_id": med["_id"]},
                        {"$set": {"image_url": None}}  # topilmadi deb belgilash
                    )
                    not_found += 1
                    logger.warning(f"✗ {med['name_uz'][:35]} — rasm topilmadi")

                await asyncio.sleep(0.3)  # Wikipedia rate limit

        tasks = [process_one(m) for m in medicines]
        await asyncio.gather(*tasks)

    logger.success(
        f"Tayyor! {found} ta rasm topildi | {not_found} ta topilmadi | "
        f"Jami: {found + not_found} ta"
    )
    await close_db()


if __name__ == "__main__":
    asyncio.run(run())
