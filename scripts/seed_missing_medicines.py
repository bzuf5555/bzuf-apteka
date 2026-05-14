"""
O'zbekiston dorixonalarida keng tarqalgan, lekin bazada yo'q dorilar.
Asosan: nevrolo giya, yurak-qon tomir, bolalar, sovuq-gripp, bo'g'iz, jigar,
venalar, ko'z/quloq tomchilari, kombinatsiyali analgetiklar.
"""
import asyncio, random, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from bot.database.connection import get_db, close_db
from bot.database.models import MEDICINES, PHARMACIES, INVENTORY

EXTRA_MEDICINES = [
    # ── Nevrologiya / Qon aylanishi ───────────────────────────────────────────
    ("Mexidol 125mg №30", "Мексидол 125мг №30", "ethylmethylhydroxypyridine succinate",
     "Neyroprotektiv", "tablet", "125mg", "30 ta",
     ["mexidol", "meksidol", "ethylmethylhydroxypyridine"], 45_000, 90_000, True),

    ("Cavinton 5mg №50", "Кавинтон 5мг №50", "vinpocetine",
     "Miya qon aylanishi", "tablet", "5mg", "50 ta",
     ["cavinton", "kavinton", "vinpocetin", "vinpocetine"], 35_000, 68_000, True),

    ("Mildronate 500mg №60", "Милдронат 500мг №60", "meldonium",
     "Kardioprotektiv/Metabolik", "capsule", "500mg", "60 ta",
     ["mildronate", "mildronat", "meldonium"], 65_000, 125_000, True),

    ("Troxevasin gel 2% 40g", "Троксевазин гель 2% 40г", "troxerutin",
     "Venotonik (tashqi)", "gel", "2%", "40g",
     ["troxevasin", "troksevazin", "troxerutin", "lyoton"], 28_000, 55_000, False),

    ("Troxevasin kapsul №50", "Троксевазин капс №50", "troxerutin",
     "Venotonik", "capsule", "300mg", "50 ta",
     ["troxevasin", "troksevazin"], 45_000, 88_000, True),

    ("Lyoton 1000 gel 50g", "Лиотон 1000 гель 50г", "heparin",
     "Venotonik (tashqi)", "gel", "1000 ME/g", "50g",
     ["lyoton", "lioton", "heparin gel", "trombless"], 42_000, 80_000, False),

    ("Piracetam 800mg №60", "Пирацетам 800мг №60", "piracetam",
     "Nootropik", "capsule", "800mg", "60 ta",
     ["piracetam", "piratsetam", "nootropil"], 22_000, 45_000, False),

    ("Phenibut 250mg №20", "Фенибут 250мг №20", "phenibut",
     "Nootropik/Anxiolitik", "tablet", "250mg", "20 ta",
     ["fenibut", "phenibut", "noofen"], 12_000, 25_000, True),

    # ── Jigar preparatlari ────────────────────────────────────────────────────
    ("Essentiale Forte N №30", "Эссенциале Форте Н №30", "essential phospholipids",
     "Gepaprotektiv", "capsule", "300mg", "30 ta",
     ["essentiale", "essentiale forte", "gepabene"], 68_000, 130_000, False),

    ("Gepabene №60", "Гепабене №60", "fumaria+milk thistle",
     "Gepaprotektiv (fitovosita)", "capsule", "", "60 ta",
     ["gepabene", "karsil", "silymarin"], 42_000, 82_000, False),

    ("Karsil 35mg №90", "Карсил 35мг №90", "silymarin",
     "Gepaprotektiv", "coated tablet", "35mg", "90 ta",
     ["karsil", "silymarin", "legalon"], 38_000, 75_000, False),

    ("Ursofalk 250mg №50", "Урсофальк 250мг №50", "ursodeoxycholic acid",
     "Gepaprotektiv/O't toshi", "capsule", "250mg", "50 ta",
     ["ursofalk", "ursohol", "ursodeoxycholic acid", "udca"], 95_000, 185_000, True),

    # ── Bolalar preparatlari ──────────────────────────────────────────────────
    ("Nurofen bolalar 100ml sirobi", "Нурофен детский сироп 100мл", "ibuprofen",
     "Bolalar analgetiki", "syrup", "100mg/5ml", "100ml",
     ["nurofen children", "ibuprofen children", "nurofen bolalar"], 38_000, 65_000, False),

    ("Calpol 120mg/5ml 100ml", "Калпол 120мг/5мл 100мл", "paracetamol",
     "Bolalar analgetiki", "syrup", "120mg/5ml", "100ml",
     ["calpol", "paracetamol bolalar", "panadol baby", "tylenol children"], 25_000, 48_000, False),

    ("Panadol Baby 125mg suppositories №10", "Панадол Беби суппозитории №10", "paracetamol",
     "Bolalar analgetiki (sham)", "suppository", "125mg", "10 ta",
     ["panadol baby", "paracetamol sham", "efferalgan baby"], 28_000, 52_000, False),

    # ── Sovuq/Grip preparatlari ───────────────────────────────────────────────
    ("Theraflu Limon 1 doza", "Терафлю Лимон 1 пак", "paracetamol+pheniramine+phenylephrine",
     "Sovuq preparati", "powder", "", "1 ta paket",
     ["theraflu", "teraflu", "coldrex", "rinza", "maxicold"], 12_000, 22_000, False),

    ("Coldrex Night №12", "Колдрекс Найт №12", "paracetamol+promethazine+pholcodine",
     "Sovuq preparati (tunda)", "tablet", "", "12 ta",
     ["coldrex", "koldreks"], 38_000, 68_000, False),

    ("Rinza №10", "Ринза №10", "paracetamol+phenylephrine+caffeine",
     "Sovuq preparati", "tablet", "", "10 ta",
     ["rinza", "grippeks"], 18_000, 35_000, False),

    # ── Bo'g'iz preparatlari ──────────────────────────────────────────────────
    ("Strepsils №24", "Стрепсилс №24", "amylmetacresol+dichlorobenzyl alcohol",
     "Bo'g'iz antiseptigi", "lozenge", "", "24 ta",
     ["strepsils", "strepsels", "faringosept"], 28_000, 52_000, False),

    ("Faringosept №10", "Фарингосепт №10", "ambazone",
     "Bo'g'iz antiseptigi", "lozenge", "10mg", "10 ta",
     ["faringosept", "pharyngosept", "ambazone"], 12_000, 22_000, False),

    ("Septefril №10", "Септефрил №10", "dequalinium chloride",
     "Bo'g'iz antiseptigi", "tablet", "", "10 ta",
     ["septefril", "septifril"], 10_000, 20_000, False),

    ("Gramicidin S №20", "Граммидин С №20", "gramicidin+cetylpyridinium",
     "Bo'g'iz antiseptigi", "lozenge", "", "20 ta",
     ["gramicidin", "grammidine", "grammidin"], 22_000, 42_000, False),

    # ── Siydik yo'llari (qo'shimcha) ──────────────────────────────────────────
    ("Furagin 50mg №30", "Фурагин 50мг №30", "furazidin",
     "Siydik yo'llari antiseptigi", "tablet", "50mg", "30 ta",
     ["furagin", "furazidine", "furadonin", "nitrofurantoin"], 12_000, 25_000, True),

    ("Biseptol 480mg №20", "Бисептол 480мг №20", "co-trimoxazole",
     "Antibiotik (sulfonamid)", "tablet", "480mg", "20 ta",
     ["biseptol", "biseptor", "co-trimoxazole", "bactrim", "septrin"], 12_000, 25_000, True),

    # ── Antiseptiklar (qo'shimcha) ─────────────────────────────────────────────
    ("Streptotsid malhami 10% 25g", "Стрептоцид мазь 10% 25г", "sulfanilamide",
     "Tashqi antiseptik", "ointment", "10%", "25g",
     ["streptotsid", "sulfanilamide", "streptocid"], 8_000, 16_000, False),

    ("Furasilin 0.02% eritma 200ml", "Фурацилин 0,02% р-р 200мл", "nitrofural",
     "Tashqi antiseptik", "solution", "0.02%", "200ml",
     ["furasilin", "furacilin", "nitrofural"], 8_000, 16_000, False),

    # ── Ko'z/quloq tomchilari (qo'shimcha) ────────────────────────────────────
    ("Vigamox ko'z tomchisi 5ml", "Вигамокс глазные капли 5мл", "moxifloxacin",
     "Ko'z tomchisi (antibiotik)", "eye drops", "0.5%", "5ml",
     ["vigamox", "moksiflokatsin", "moxifloxacin"], 42_000, 80_000, True),

    ("Floxal ko'z tomchisi 5ml", "Флоксал глазные капли 5мл", "ofloxacin",
     "Ko'z tomchisi (antibiotik)", "eye drops", "0.3%", "5ml",
     ["floxal", "ofloxacin", "oflotsatsin eye"], 35_000, 65_000, True),

    ("Sofradex quloq/ko'z 8ml", "Софрадекс уш/глаз 8мл", "framycetin+gramicidin+dexamethasone",
     "Quloq va ko'z tomchisi", "drops", "", "8ml",
     ["sofradex", "sofradeks"], 32_000, 62_000, True),

    # ── Kombinatsiyali analgetiklar ────────────────────────────────────────────
    ("Pentalgin №12", "Пенталгин №12", "paracetamol+metamizole+caffeine",
     "Kombinatsiyali analgetik", "tablet", "", "12 ta",
     ["pentalgin", "pentalgin forte", "kombinalgin"], 15_000, 28_000, False),

    ("Sedalgin Neo №10", "Седалгин Нео №10", "paracetamol+caffeine+codeine",
     "Kombinatsiyali analgetik", "tablet", "", "10 ta",
     ["sedalgin", "sedalgin neo", "spazgan"], 12_000, 25_000, True),

    # ── Tizimli immunomodulyatorlar ───────────────────────────────────────────
    ("Immunal 100ml tomchilari", "Иммунал капли 100мл", "echinacea purpurea",
     "Immunomodulyator (fitovosita)", "drops", "", "100ml",
     ["immunal", "imunal", "echinacea", "echinaceya"], 28_000, 55_000, False),

    ("Lavomax 125mg №6", "Лавомакс 125мг №6", "tilorone",
     "Antiviral/Immunomodulyator", "tablet", "125mg", "6 ta",
     ["lavomax", "tiloron", "amixin"], 38_000, 72_000, True),

    # ── Suyak zichligi / Osteoporoz ───────────────────────────────────────────
    ("Osteogenon №40", "Остеогенон №40", "ossein+hydroxyapatite",
     "Osteoporoz preparati", "tablet", "", "40 ta",
     ["osteogenon", "osteogenon ossein"], 55_000, 105_000, True),

    ("Alfacalcidol 0.5mcg №30", "Альфакальцидол 0,5мкг №30", "alfacalcidol",
     "Vitamin D3 aktiv shakli", "capsule", "0.5mcg", "30 ta",
     ["alfacalcidol", "alpha-d3", "etalpha"], 42_000, 82_000, True),

    # ── Gemorroyga qarshi ─────────────────────────────────────────────────────
    ("Posterizan Plus №10 sham", "Постеризан Плюс №10 суп", "hydrocortisone+escherichia coli",
     "Gemorroy (sham)", "suppository", "", "10 ta",
     ["posterizan", "posterisan", "proctosan"], 45_000, 88_000, False),

    ("Proctosan malhami 30g", "Проктозан мазь 30г", "bufexamac+bismuth+titanium+lidocaine",
     "Gemorroy (malham)", "ointment", "", "30g",
     ["proctosan", "proktosan", "hepatrombin"], 38_000, 72_000, False),

    # ── Qo'shimcha antibiotiklar ──────────────────────────────────────────────
    ("Lincomycin 500mg №20", "Линкомицин 500мг №20", "lincomycin",
     "Antibiotik (Linkozamid)", "capsule", "500mg", "20 ta",
     ["lincomycin", "linkomitsin", "neloren"], 18_000, 38_000, True),

    ("Gentamicin 40mg/ml №10 amp", "Гентамицин 40мг/мл №10 амп", "gentamicin",
     "Antibiotik (Aminoglikozid)", "injection", "40mg/ml", "10 ta ampula",
     ["gentamicin", "gentamitsin"], 12_000, 25_000, True),

    ("Furazolidone 50mg №20", "Фуразолидон 50мг №20", "furazolidone",
     "Ichak antiseptigi", "tablet", "50mg", "20 ta",
     ["furazolidon", "nifuroxazide", "furazolidone"], 8_000, 18_000, True),

    # ── Qo'shimcha oshqozon dorilar ───────────────────────────────────────────
    ("Maalox №20 saqich", "Маалокс №20 таб", "aluminium hydroxide+magnesium hydroxide",
     "Antatsid", "chewable tablet", "", "20 ta",
     ["maalox", "maalox nano", "aluminium magnesium"], 22_000, 42_000, False),

    ("De-Nol 120mg №56", "Де-Нол 120мг №56", "bismuth tripotassium dicitrate",
     "Gastroduodenal yaraga qarshi", "tablet", "120mg", "56 ta",
     ["de-nol", "denol", "bismuth", "vikalin"], 75_000, 145_000, True),

    ("Rebamipid 100mg №30", "Ребамипид 100мг №30", "rebamipide",
     "Gastroduodenal himoyachi", "tablet", "100mg", "30 ta",
     ["rebamipid", "rebagen", "mucosta"], 55_000, 105_000, True),

    # ── Teri kasalliklari ─────────────────────────────────────────────────────
    ("Akriderm GK 15g", "Акридерм ГК 15г", "betamethasone+gentamicin+clotrimazole",
     "Tashqi kombinatsiyali", "cream", "", "15g",
     ["akriderm", "triderm", "beloderm"], 22_000, 42_000, True),

    ("Sinaflan malhami 15g", "Синафлан мазь 15г", "fluocinolone acetonide",
     "Tashqi kortikosteroid", "ointment", "0.025%", "15g",
     ["sinaflan", "fluocinolone", "celestoderm"], 8_000, 18_000, True),

    ("Contractubex gel 30g", "Контрактубекс гель 30г", "onion extract+heparin+allantoin",
     "Tirik to'qima regeneranti (chandiq)", "gel", "", "30g",
     ["contractubex", "kontraktubeks", "scar gel"], 55_000, 105_000, False),
]


async def run():
    db = await get_db()

    # Mavjud dorilarni tekshirish
    existing_generics = set()
    async for med in db[MEDICINES].find({}, {"generic_name": 1, "dosage": 1, "pack_size": 1}):
        key = f"{med.get('generic_name','')}|{med.get('dosage','default')}|{med.get('pack_size','')}"
        existing_generics.add(key)

    new_meds = []
    for row in EXTRA_MEDICINES:
        (name_uz, name_ru, generic_name, category, dosage_form,
         dosage, pack_size, synonyms, price_min, price_max, rx) = row

        key = f"{generic_name}|{dosage or 'default'}|{pack_size}"
        if key in existing_generics:
            continue

        new_meds.append({
            "name_uz": name_uz, "name_ru": name_ru, "generic_name": generic_name,
            "category": category, "dosage_form": dosage_form, "dosage": dosage,
            "pack_size": pack_size, "synonyms": synonyms,
            "price_min": price_min, "price_max": price_max,
            "requires_prescription": rx,
        })
        existing_generics.add(key)

    if not new_meds:
        logger.info("Barcha qo'shimcha dorilar allaqachon mavjud")
        await close_db()
        return

    result = await db[MEDICINES].insert_many(new_meds)
    inserted_ids = result.inserted_ids
    logger.success(f"{len(inserted_ids)} ta yangi dori qo'shildi")

    # Haqiqiy dorixonalarga qo'shimcha dorilarni ulash
    prices = [8_000, 12_000, 18_000, 25_000, 35_000, 45_000, 55_000, 68_000, 85_000]
    ph_cursor = db[PHARMACIES].find({}, {"_id": 1})
    ph_ids = [doc["_id"] async for doc in ph_cursor]

    random.seed(99)
    inv_docs = []
    for ph_id in ph_ids:
        k = random.randint(int(len(inserted_ids) * 0.5), len(inserted_ids))
        selected = random.sample(inserted_ids, k=k)
        for med_id in selected:
            inv_docs.append({
                "pharmacy_id": ph_id,
                "medicine_id": med_id,
                "price": random.choice(prices),
                "in_stock": True,
                "updated_at": datetime.now(timezone.utc),
            })

    if inv_docs:
        BATCH = 3000
        for i in range(0, len(inv_docs), BATCH):
            await db[INVENTORY].insert_many(inv_docs[i:i+BATCH], ordered=False)

    total_med = await db[MEDICINES].count_documents({})
    total_inv = await db[INVENTORY].count_documents({})
    logger.success(f"Jami: {total_med} ta dori | {total_inv:,} ta inventar")
    await close_db()


if __name__ == "__main__":
    asyncio.run(run())
