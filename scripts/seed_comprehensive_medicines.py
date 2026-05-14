"""
Keng qamrovli dori bazasi — O'zbekiston dorixonalaridagi haqiqiy narxlar.

Narxlar O'zbekiston farmatsevtika bozori (2024-2025) asosida:
- Dori-darmon.uz (davlat narx ro'yxati)
- aptek.uz, apteka.uz (real bozor narxlari)
- Savdo ustamasi: 15-30% (distribyutor → dorixona)

MUHIM: Narxlar taxminiy. Har bir dorixona o'z narxini belgilaydi.
price_min: bozordagi eng arzon narx (odatda generik)
price_max: bozordagi eng qimmat narx (odatda brendli)

Narx birligi: UZS (O'zbek so'mi)
"""
import asyncio
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from bot.database.connection import get_db, close_db
from bot.database.models import create_indexes, MEDICINES, PHARMACIES, INVENTORY

# ─────────────────────────────────────────────────────────────────────────────
# DORILAR RO'YXATI — (name_uz, name_ru, generic_name, category, dosage_form,
#                     dosage, pack_size, synonyms, price_min, price_max, rx)
# rx=True → retsept bilan sotiladi
# ─────────────────────────────────────────────────────────────────────────────
MEDICINES_DATA = [

    # ── Analgetik / Antipiretik ───────────────────────────────────────────────
    ("Paracetamol 500mg №10", "Парацетамол 500мг №10", "paracetamol",
     "Analgetik/Antipiretik", "tablet", "500mg", "10 ta",
     ["acetaminophen", "paratsetamol", "efferalgan"], 8_000, 14_000, False),

    ("Paracetamol 500mg №20", "Парацетамол 500мг №20", "paracetamol",
     "Analgetik/Antipiretik", "tablet", "500mg", "20 ta",
     ["paratsetamol"], 14_000, 25_000, False),

    ("Panadol Extra №12", "Панадол Экстра №12", "paracetamol+caffeine",
     "Analgetik/Antipiretik", "tablet", "500mg+65mg", "12 ta",
     ["panadol"], 28_000, 45_000, False),

    ("Ibuprofen 200mg №10", "Ибупрофен 200мг №10", "ibuprofen",
     "Analgetik/NSAID", "tablet", "200mg", "10 ta",
     ["ibuprofin", "ibufen"], 12_000, 22_000, False),

    ("Ibuprofen 400mg №10", "Ибупрофен 400мг №10", "ibuprofen",
     "Analgetik/NSAID", "tablet", "400mg", "10 ta",
     ["ibuprofin", "nurofen"], 16_000, 28_000, False),

    ("Nurofen Express 400mg №10", "Нурофен Экспресс 400мг №10", "ibuprofen",
     "Analgetik/NSAID", "capsule", "400mg", "10 ta",
     ["nurofen", "ibuprofen"], 38_000, 58_000, False),

    ("Aspirin 500mg №10", "Аспирин 500мг №10", "acetylsalicylic acid",
     "Analgetik/Antipiretik", "tablet", "500mg", "10 ta",
     ["atsetilsalisin", "aspirin"], 8_000, 16_000, False),

    ("Aspirin Cardio 100mg №28", "Аспирин Кардио 100мг №28", "acetylsalicylic acid",
     "Kardiovaskulyar", "tablet", "100mg", "28 ta",
     ["aspirin cardio", "cardioaspirin"], 22_000, 38_000, False),

    ("Analgin 500mg №10", "Анальгин 500мг №10", "metamizole sodium",
     "Analgetik", "tablet", "500mg", "10 ta",
     ["metamizol", "baralgin"], 6_000, 12_000, False),

    ("Ketorol 10mg №20", "Кеторол 10мг №20", "ketorolac",
     "Analgetik/NSAID", "tablet", "10mg", "20 ta",
     ["ketorolak", "ketanov"], 35_000, 60_000, False),

    ("Nimesulid 100mg №20", "Нимесулид 100мг №20", "nimesulide",
     "Analgetik/NSAID", "tablet", "100mg", "20 ta",
     ["nimesil", "nimusid", "nise"], 25_000, 45_000, False),

    ("Diclofenac 50mg №20", "Диклофенак 50мг №20", "diclofenac",
     "Analgetik/NSAID", "tablet", "50mg", "20 ta",
     ["diklofenac", "voltaren", "ortofen"], 12_000, 25_000, False),

    ("Diclofenac gel 1% 50g", "Диклофенак гель 1% 50г", "diclofenac",
     "Tashqi/NSAID", "gel", "1%", "50g",
     ["voltaren gel", "diklak"], 28_000, 55_000, False),

    # ── Spazmolitik ──────────────────────────────────────────────────────────
    ("No-Shpa 40mg №10", "Но-Шпа 40мг №10", "drotaverine",
     "Spazmolitik", "tablet", "40mg", "10 ta",
     ["drotaverin", "noshpa", "nospa"], 12_000, 22_000, False),

    ("No-Shpa 40mg №24", "Но-Шпа 40мг №24", "drotaverine",
     "Spazmolitik", "tablet", "40mg", "24 ta",
     ["drotaverin", "noshpa"], 25_000, 45_000, False),

    ("No-Shpa Forte 80mg №10", "Но-Шпа Форте 80мг №10", "drotaverine",
     "Spazmolitik", "tablet", "80mg", "10 ta",
     ["noshpa forte"], 20_000, 38_000, False),

    ("Papaverin 40mg №20", "Папаверин 40мг №20", "papaverine",
     "Spazmolitik", "tablet", "40mg", "20 ta",
     ["papaverin"], 7_000, 14_000, False),

    ("Buscopan 10mg №20", "Бускопан 10мг №20", "hyoscine",
     "Spazmolitik", "tablet", "10mg", "20 ta",
     ["giostin", "buskopan"], 38_000, 65_000, False),

    # ── Antibiotiklar ─────────────────────────────────────────────────────────
    ("Amoxicillin 500mg №16", "Амоксициллин 500мг №16", "amoxicillin",
     "Antibiotik (Penissillin)", "capsule", "500mg", "16 ta",
     ["amoksitsillin", "flemoxin", "ospamox"], 22_000, 42_000, True),

    ("Amoksiklav 625mg №14", "Амоксиклав 625мг №14", "amoxicillin+clavulanate",
     "Antibiotik (Penissillin)", "tablet", "500mg+125mg", "14 ta",
     ["augmentin", "amoxiclav", "panklav"], 85_000, 155_000, True),

    ("Augmentin 875mg №14", "Аугментин 875мг №14", "amoxicillin+clavulanate",
     "Antibiotik (Penissillin)", "tablet", "875mg+125mg", "14 ta",
     ["amoksiklav", "augmentin"], 120_000, 200_000, True),

    ("Azithromycin 500mg №3", "Азитромицин 500мг №3", "azithromycin",
     "Antibiotik (Makrolid)", "tablet", "500mg", "3 ta",
     ["azitromitsin", "hemomycin", "zitrolid"], 32_000, 65_000, True),

    ("Sumamed 500mg №3", "Сумамед 500мг №3", "azithromycin",
     "Antibiotik (Makrolid)", "tablet", "500mg", "3 ta",
     ["azithromycin", "zithromax"], 80_000, 150_000, True),

    ("Ciprofloxacin 500mg №10", "Ципрофлоксацин 500мг №10", "ciprofloxacin",
     "Antibiotik (Ftorxinolon)", "tablet", "500mg", "10 ta",
     ["tsiprofloksatsin", "cipro", "siflox"], 32_000, 65_000, True),

    ("Levofloxacin 500mg №10", "Левофлоксацин 500мг №10", "levofloxacin",
     "Antibiotik (Ftorxinolon)", "tablet", "500mg", "10 ta",
     ["levofloksatsin", "tavanic", "lebel"], 55_000, 100_000, True),

    ("Metronidazol 250mg №20", "Метронидазол 250мг №20", "metronidazole",
     "Antibiotik (Nitroimidazol)", "tablet", "250mg", "20 ta",
     ["metronidazola", "flagyl", "trichopol"], 7_000, 16_000, True),

    ("Metronidazol 500mg №10", "Метронидазол 500мг №10", "metronidazole",
     "Antibiotik (Nitroimidazol)", "tablet", "500mg", "10 ta",
     ["metronidazola", "flagyl"], 10_000, 22_000, True),

    ("Doxycycline 100mg №10", "Доксициклин 100мг №10", "doxycycline",
     "Antibiotik (Tetratsiklin)", "capsule", "100mg", "10 ta",
     ["doksitsiklin", "vibramycin"], 18_000, 38_000, True),

    ("Klindamisin 300mg №16", "Клиндамицин 300мг №16", "clindamycin",
     "Antibiotik (Linkozamid)", "capsule", "300mg", "16 ta",
     ["klindamitsin", "dalacin"], 65_000, 120_000, True),

    ("Ceftriaxone 1g №1 amp", "Цефтриаксон 1г №1 амп", "ceftriaxone",
     "Antibiotik (Tseyfalosporin)", "injection", "1g", "1 ta ampula",
     ["tseftriakson", "rocephin"], 20_000, 40_000, True),

    ("Fluconazole 150mg №1", "Флуконазол 150мг №1", "fluconazole",
     "Antifungal", "capsule", "150mg", "1 ta",
     ["flukonazol", "diflucan", "mycosyst"], 16_000, 32_000, True),

    ("Fluconazole 150mg №7", "Флуконазол 150мг №7", "fluconazole",
     "Antifungal", "capsule", "150mg", "7 ta",
     ["flukonazol", "diflucan"], 80_000, 150_000, True),

    # ── Kardiovaskulyar ───────────────────────────────────────────────────────
    ("Bisoprolol 5mg №30", "Бисопролол 5мг №30", "bisoprolol",
     "Beta-bloker", "tablet", "5mg", "30 ta",
     ["bisoprolo", "concor", "bisogamma"], 22_000, 48_000, True),

    ("Bisoprolol 10mg №30", "Бисопролол 10мг №30", "bisoprolol",
     "Beta-bloker", "tablet", "10mg", "30 ta",
     ["bisoprolo", "concor"], 28_000, 58_000, True),

    ("Concor 5mg №30", "Конкор 5мг №30", "bisoprolol",
     "Beta-bloker", "tablet", "5mg", "30 ta",
     ["bisoprolol"], 55_000, 100_000, True),

    ("Amlodipine 5mg №30", "Амлодипин 5мг №30", "amlodipine",
     "Kaltsiy-kanal blokatori", "tablet", "5mg", "30 ta",
     ["amlodipin", "norvasc", "amlovask"], 18_000, 40_000, True),

    ("Amlodipine 10mg №30", "Амлодипин 10мг №30", "amlodipine",
     "Kaltsiy-kanal blokatori", "tablet", "10mg", "30 ta",
     ["amlodipin", "norvasc"], 25_000, 55_000, True),

    ("Enalapril 10mg №20", "Эналаприл 10мг №20", "enalapril",
     "AKF ingibitori", "tablet", "10mg", "20 ta",
     ["enap", "enam", "enalapril"], 14_000, 28_000, True),

    ("Lisinopril 10mg №28", "Лизиноприл 10мг №28", "lisinopril",
     "AKF ingibitori", "tablet", "10mg", "28 ta",
     ["lizinoprip", "diroton", "listril"], 18_000, 38_000, True),

    ("Losartan 50mg №30", "Лозартан 50мг №30", "losartan",
     "ARB", "tablet", "50mg", "30 ta",
     ["lozartan", "kozaar", "loriста"], 32_000, 68_000, True),

    ("Atorvastatin 20mg №30", "Аторвастатин 20мг №30", "atorvastatin",
     "Statin", "tablet", "20mg", "30 ta",
     ["atorvastatin", "lipitor", "torvakard"], 38_000, 78_000, True),

    ("Rosuvastatin 20mg №30", "Розувастатин 20мг №30", "rosuvastatin",
     "Statin", "tablet", "20mg", "30 ta",
     ["rozuvastatin", "crestor", "mertenil"], 52_000, 105_000, True),

    ("Validol №10", "Валидол №10", "validol",
     "Yurak dori (simptomatik)", "tablet", "60mg", "10 ta",
     ["validola"], 5_000, 12_000, False),

    ("Corvalol 25ml", "Корвалол 25мл", "phenobarbital+peppermint",
     "Yurak dori (simptomatik)", "drops", "", "25ml",
     ["korvalol", "corvalolum"], 10_000, 20_000, False),

    ("Nitroglycerin 0.5mg №40", "Нитроглицерин 0,5мг №40", "nitroglycerin",
     "Antianginal", "tablet", "0.5mg", "40 ta",
     ["nitroglitserin", "nitrocor"], 8_000, 18_000, True),

    ("Warfarin 5mg №50", "Варфарин 5мг №50", "warfarin",
     "Antikoagulyant", "tablet", "5mg", "50 ta",
     ["varfarin", "coumadin"], 18_000, 38_000, True),

    ("Klopidogrel 75mg №28", "Клопидогрель 75мг №28", "clopidogrel",
     "Antiagregant", "tablet", "75mg", "28 ta",
     ["klopidogrel", "plavix", "zyllt"], 52_000, 100_000, True),

    ("Digoxin 0.25mg №30", "Дигоксин 0,25мг №30", "digoxin",
     "Kardiotik glikozid", "tablet", "0.25mg", "30 ta",
     ["digoksin"], 10_000, 22_000, True),

    # ── Oshqozon-ichak ────────────────────────────────────────────────────────
    ("Omeprazol 20mg №30", "Омепразол 20мг №30", "omeprazole",
     "Oshqozon dori (PPI)", "capsule", "20mg", "30 ta",
     ["omeprazola", "losek", "omez", "ultop"], 28_000, 58_000, False),

    ("Omeprazol 40mg №14", "Омепразол 40мг №14", "omeprazole",
     "Oshqozon dori (PPI)", "capsule", "40mg", "14 ta",
     ["omez", "losek"], 25_000, 48_000, False),

    ("Pantoprazol 40mg №28", "Пантопразол 40мг №28", "pantoprazole",
     "Oshqozon dori (PPI)", "tablet", "40mg", "28 ta",
     ["pantoprazola", "nolpaza", "controloc"], 38_000, 75_000, False),

    ("Esomeprazol 40mg №14", "Эзомепразол 40мг №14", "esomeprazole",
     "Oshqozon dori (PPI)", "capsule", "40mg", "14 ta",
     ["nexium", "ezomeprazol", "emanera"], 55_000, 100_000, False),

    ("Famotidin 40mg №20", "Фамотидин 40мг №20", "famotidine",
     "Oshqozon dori (H2)", "tablet", "40mg", "20 ta",
     ["famotidine", "quamatel", "ulfamid"], 16_000, 32_000, False),

    ("Mezim Forte №20", "Мезим Форте №20", "pancreatin",
     "Ferment preparati", "tablet", "10000 Ed", "20 ta",
     ["mezim", "panzinorm", "pancreatin"], 22_000, 42_000, False),

    ("Creon 10000 №25", "Креон 10000 №25", "pancreatin",
     "Ferment preparati", "capsule", "10000 Ed", "25 ta",
     ["creon", "kreon"], 80_000, 150_000, False),

    ("Lineks №16", "Линекс №16", "probiotic",
     "Probiotik", "capsule", "", "16 ta",
     ["linex", "acidolac"], 42_000, 78_000, False),

    ("Bifiform №30", "Бифиформ №30", "probiotic",
     "Probiotik", "capsule", "", "30 ta",
     ["bifiform", "bifidumbacterin"], 52_000, 98_000, False),

    ("Laktiale №30", "Лактиале №30", "probiotic",
     "Probiotik", "capsule", "", "30 ta",
     ["laktiale", "probiotic"], 55_000, 100_000, False),

    ("Loperamid 2mg №20", "Лоперамид 2мг №20", "loperamide",
     "Antidiareylik", "tablet", "2mg", "20 ta",
     ["loperamid", "imodium", "lopedium"], 10_000, 22_000, False),

    ("Immodium №6", "Имодиум №6", "loperamide",
     "Antidiareylik", "tablet", "2mg", "6 ta",
     ["imodium", "loperamid"], 24_000, 45_000, False),

    ("Smekta №10 sach", "Смекта №10 пак", "diosmectite",
     "Enterosorbent", "powder", "3g", "10 ta paket",
     ["smekta", "diosmektit"], 32_000, 62_000, False),

    ("Enterosgel 225g", "Энтеросгель 225г", "polymethylsiloxane polyhydrate",
     "Enterosorbent", "gel", "", "225g",
     ["enterosgel", "polyphepan"], 45_000, 80_000, False),

    ("Faol ko'mir №50", "Активированный уголь №50", "activated charcoal",
     "Enterosorbent", "tablet", "250mg", "50 ta",
     ["aktiv ugol", "carbo activatus"], 5_000, 11_000, False),

    ("Bisacodil 5mg №30", "Бисакодил 5мг №30", "bisacodyl",
     "Ichi keltirgich", "tablet", "5mg", "30 ta",
     ["bisacodyl", "dulcolax"], 10_000, 22_000, False),

    ("Lactulose sirobi 200ml", "Лактулоза сироп 200мл", "lactulose",
     "Ichi keltirgich", "syrup", "667g/l", "200ml",
     ["duphalac", "laktuloza", "normaze"], 28_000, 55_000, False),

    ("Gastal №30", "Гасталь №30", "antacid",
     "Antatsid", "tablet", "", "30 ta",
     ["gastal", "almagel", "maalox"], 32_000, 58_000, False),

    ("Domperidon 10mg №30", "Домперидон 10мг №30", "domperidone",
     "Prokinetik", "tablet", "10mg", "30 ta",
     ["domperidon", "motilium", "motiлак"], 22_000, 45_000, False),

    ("Metoklopramid 10mg №50", "Метоклопрамид 10мг №50", "metoclopramide",
     "Prokinetik/antiemetik", "tablet", "10mg", "50 ta",
     ["metoklopramid", "cerucal", "raglan"], 12_000, 28_000, False),

    # ── Nafas yo'llari / Allergiya ────────────────────────────────────────────
    ("Loratadin 10mg №10", "Лоратадин 10мг №10", "loratadine",
     "Antigistamin", "tablet", "10mg", "10 ta",
     ["loratadin", "claritin", "loridin", "claritine"], 10_000, 22_000, False),

    ("Cetirizin 10mg №10", "Цетиризин 10мг №10", "cetirizine",
     "Antigistamin", "tablet", "10mg", "10 ta",
     ["tsetirizin", "zyrtec", "zirtec", "letizen"], 12_000, 26_000, False),

    ("Desloratadin 5mg №10", "Дезлоратадин 5мг №10", "desloratadine",
     "Antigistamin", "tablet", "5mg", "10 ta",
     ["dezloratadin", "erius", "aerius"], 28_000, 58_000, False),

    ("Suprastin 25mg №20", "Супрастин 25мг №20", "chloropyramine",
     "Antigistamin (1-avlod)", "tablet", "25mg", "20 ta",
     ["suprastin", "xloropiramin"], 10_000, 22_000, False),

    ("Fenistil tomchilar 20ml", "Фенистил капли 20мл", "dimethindene",
     "Antigistamin (1-avlod)", "drops", "0.1%", "20ml",
     ["fenistil", "dimethindene"], 32_000, 58_000, False),

    ("Ambroksol 30mg №20", "Амброксол 30мг №20", "ambroxol",
     "Mukolitik/Ekspektorant", "tablet", "30mg", "20 ta",
     ["ambroksol", "lazolvan", "mucosolvan", "flavamed"], 10_000, 22_000, False),

    ("Lazolvan sirop 100ml", "Лазолван сироп 100мл", "ambroxol",
     "Mukolitik/Ekspektorant", "syrup", "15mg/5ml", "100ml",
     ["ambroksol sirop", "mucosolvan", "flavamed"], 35_000, 65_000, False),

    ("ACC 200 №20 sach", "АЦЦ 200 №20 пак", "acetylcysteine",
     "Mukolitik", "powder", "200mg", "20 ta paket",
     ["atsetilsistein", "fluimucil", "acc"], 35_000, 65_000, False),

    ("Bromgeksin 8mg №25", "Бромгексин 8мг №25", "bromhexine",
     "Mukolitik", "tablet", "8mg", "25 ta",
     ["bromgeksin", "solvin"], 10_000, 20_000, False),

    ("Erespal 80mg №30", "Эреспал 80мг №30", "fenspiride",
     "Nafas yo'llari yallig'lanishiga qarshi", "tablet", "80mg", "30 ta",
     ["erespal", "fenspirid", "elospir"], 45_000, 88_000, False),

    ("Sinekod tomchilar 20ml", "Синекод капли 20мл", "butamirate",
     "Yo'talni bosuvchi", "drops", "5mg/ml", "20ml",
     ["sinekod", "butamirat"], 32_000, 62_000, False),

    ("Codelac Bronho №20", "Кодeлак Бронхо №20", "ambroxol+sodium glycyrrhizinate",
     "Yo'talga qarshi", "tablet", "", "20 ta",
     ["codelac", "kodelak"], 18_000, 35_000, False),

    ("Naftizin 0.1% 10ml", "Нафтизин 0,1% 10мл", "naphazoline",
     "Burun tomchisi (vazokonstriktor)", "drops", "0.1%", "10ml",
     ["naftizin", "sanorin"], 4_000, 10_000, False),

    ("Otrivin 0.1% spray 10ml", "Отривин 0,1% спрей 10мл", "xylometazoline",
     "Burun spreyi (vazokonstriktor)", "spray", "0.1%", "10ml",
     ["otrivin", "ksimelin", "tizin"], 22_000, 42_000, False),

    ("Aqua Maris burun spreyi", "Аква Марис назальный спрей", "sea water",
     "Burun spreyi (fiziologik)", "spray", "", "30ml",
     ["aqua maris", "akvalor", "physiomer"], 25_000, 48_000, False),

    ("Rinasek burun spreyi", "Ринасек назальный спрей", "mometasone",
     "Burun spreyi (kortikosteroid)", "spray", "50mcg", "60 doza",
     ["rinasek", "nasonex", "mometason"], 45_000, 88_000, True),

    # ── Vitaminlar va Qo'shimchalar ───────────────────────────────────────────
    ("Vitamin C 1000mg №10 efferv.", "Витамин С 1000мг №10 шип", "ascorbic acid",
     "Vitamin", "effervescent tablet", "1000mg", "10 ta",
     ["askorbin kislota", "askorbinka", "cevirex"], 22_000, 42_000, False),

    ("Vitamin C 500mg №30", "Витамин С 500мг №30", "ascorbic acid",
     "Vitamin", "tablet", "500mg", "30 ta",
     ["askorbin kislota", "askovit"], 12_000, 28_000, False),

    ("Vitamin D3 1000 ME №60", "Витамин D3 1000 МЕ №60", "cholecalciferol",
     "Vitamin", "capsule", "1000 ME", "60 ta",
     ["vitamin d3", "xolekalsiferol", "vigantol", "aquadetrim"], 35_000, 68_000, False),

    ("Vitamin D3 5000 ME №60", "Витамин D3 5000 МЕ №60", "cholecalciferol",
     "Vitamin", "capsule", "5000 ME", "60 ta",
     ["vitamin d3 5000", "cholecalciferol forte"], 52_000, 100_000, False),

    ("Aquadetrim D3 tomchilar 10ml", "Аквадетрим D3 капли 10мл", "cholecalciferol",
     "Vitamin", "drops", "15000 ME/ml", "10ml",
     ["aquadetrim", "vitamin d3 tomchi"], 28_000, 52_000, False),

    ("Magne B6 №60", "Магне B6 №60", "magnesium+pyridoxine",
     "Mineral/Vitamin", "tablet", "", "60 ta",
     ["magne b6", "magnelis", "magnikum"], 55_000, 105_000, False),

    ("Kaltsiy D3 Nycomed №60", "Кальций D3 Никомед №60", "calcium+vitamin D3",
     "Mineral/Vitamin", "tablet", "500mg+200ME", "60 ta",
     ["kaltsiy d3", "calcium d3", "complivit kaltsiy"], 52_000, 98_000, False),

    ("Centrum №30", "Центрум №30", "multivitamin",
     "Multivitamin", "tablet", "", "30 ta",
     ["centrum", "multivitamin"], 52_000, 100_000, False),

    ("Vitrum №30", "Витрум №30", "multivitamin",
     "Multivitamin", "tablet", "", "30 ta",
     ["vitrum", "multivitamin"], 62_000, 118_000, False),

    ("Complivit №60", "Компливит №60", "multivitamin",
     "Multivitamin", "tablet", "", "60 ta",
     ["complivit", "multivitamin"], 32_000, 62_000, False),

    ("Omega-3 1000mg №90", "Омега-3 1000мг №90", "omega-3",
     "Qo'shimcha", "capsule", "1000mg", "90 ta",
     ["omega-3", "fish oil", "baliq yog'i"], 55_000, 105_000, False),

    ("Fol kislota 1mg №50", "Фолиевая кислота 1мг №50", "folic acid",
     "Vitamin", "tablet", "1mg", "50 ta",
     ["fol kislota", "folievaya kislota", "folibex"], 7_000, 15_000, False),

    ("Ferrum Lek №30", "Феррум Лек №30", "iron",
     "Temir preparati", "tablet", "100mg", "30 ta",
     ["ferrum lek", "temir", "maltofer", "sorbifer"], 35_000, 68_000, False),

    ("Zincit №15", "Цинцит №15", "zinc",
     "Mineral", "capsule", "15mg", "15 ta",
     ["zincit", "zinc", "rux"], 22_000, 42_000, False),

    ("Vitamin E 400 ME №30", "Витамин Е 400 МЕ №30", "tocopherol",
     "Vitamin", "capsule", "400 ME", "30 ta",
     ["vitamin e", "tokoferol", "evitol"], 22_000, 42_000, False),

    ("Berocca Perfomance №15", "Берокка Перформанс №15", "B-vitamins+C",
     "Multivitamin (effervescent)", "effervescent tablet", "", "15 ta",
     ["berocca", "B vitamini kompleks"], 42_000, 80_000, False),

    # ── Diabet dori ──────────────────────────────────────────────────────────
    ("Metformin 500mg №60", "Метформин 500мг №60", "metformin",
     "Diabet dori (Biguanid)", "tablet", "500mg", "60 ta",
     ["metformin", "glucophage", "siofor", "bagomet"], 14_000, 28_000, True),

    ("Metformin 850mg №60", "Метформин 850мг №60", "metformin",
     "Diabet dori (Biguanid)", "tablet", "850mg", "60 ta",
     ["metformin", "glucophage", "siofor"], 18_000, 36_000, True),

    ("Metformin 1000mg №60", "Метформин 1000мг №60", "metformin",
     "Diabet dori (Biguanid)", "tablet", "1000mg", "60 ta",
     ["metformin", "glucophage 1000"], 22_000, 45_000, True),

    ("Glibenclamid 5mg №50", "Глибенкламид 5мг №50", "glibenclamide",
     "Diabet dori (Sulfanilmochevina)", "tablet", "5mg", "50 ta",
     ["glibenklamid", "maninil"], 7_000, 16_000, True),

    ("Gliclazid MR 60mg №30", "Гликлазид МВ 60мг №30", "gliclazide",
     "Diabet dori (Sulfanilmochevina)", "tablet", "60mg MR", "30 ta",
     ["gliklazid", "diabeton mv", "gliclada"], 22_000, 45_000, True),

    ("Iodomarin 200 №100", "Йодомарин 200 №100", "potassium iodide",
     "Qalqonsimon bez dori", "tablet", "200mcg", "100 ta",
     ["iodomarin", "iodin", "potassium iodide"], 22_000, 45_000, False),

    ("Levotiroxin 50mcg №50", "Левотироксин 50мкг №50", "levothyroxine",
     "Tireoid gormoni", "tablet", "50mcg", "50 ta",
     ["levotiroksid", "euthyrox", "l-thyroxine"], 16_000, 35_000, True),

    ("Levotiroxin 100mcg №50", "Левотироксин 100мкг №50", "levothyroxine",
     "Tireoid gormoni", "tablet", "100mcg", "50 ta",
     ["levotiroksid", "euthyrox"], 20_000, 42_000, True),

    # ── Asab tizimi ──────────────────────────────────────────────────────────
    ("Glitsin 0.1g №50", "Глицин 0,1г №50", "glycine",
     "Nootropik/Sedativ", "tablet", "100mg", "50 ta",
     ["glitsin", "glycine", "glycised"], 8_000, 18_000, False),

    ("Nootropil 800mg №30", "Ноотропил 800мг №30", "piracetam",
     "Nootropik", "capsule", "800mg", "30 ta",
     ["piratsetam", "piracetam", "lucetam"], 32_000, 62_000, False),

    ("Phenibut 250mg №10", "Фенибут 250мг №10", "phenibut",
     "Nootropik/Anxiolitik", "tablet", "250mg", "10 ta",
     ["fenibut", "phenibut", "noofen"], 10_000, 22_000, True),

    ("Afobazol 10mg №60", "Афобазол 10мг №60", "fabomotizole",
     "Anxiolitik (dag'al sedativ emas)", "tablet", "10mg", "60 ta",
     ["afobazol", "anxiolitik"], 32_000, 62_000, False),

    ("Grandaxin 50mg №20", "Грандаксин 50мг №20", "tofisopam",
     "Anxiolitik", "tablet", "50mg", "20 ta",
     ["grandaksin", "tofizopam"], 32_000, 62_000, True),

    ("Tenoten №40", "Тенотен №40", "antibodies to brain protein",
     "Anxiolitik (gomeotopiya)", "tablet", "", "40 ta",
     ["tenoten", "stresstenil"], 32_000, 62_000, False),

    ("Diazepam 5mg №20", "Диазепам 5мг №20", "diazepam",
     "Benzodiazepin/Sedativ", "tablet", "5mg", "20 ta",
     ["diazepama", "valium", "relanium", "seduxen"], 8_000, 18_000, True),

    ("Donormil 15mg №15", "Донормил 15мг №15", "doxylamine",
     "Uyqu dori", "tablet", "15mg", "15 ta",
     ["donormil", "doksilamin", "reladorm"], 22_000, 42_000, True),

    ("Melaxen 3mg №24", "Мелаксен 3мг №24", "melatonin",
     "Uyqu dori (melatonin)", "tablet", "3mg", "24 ta",
     ["melatonin", "melaxen", "melaton"], 32_000, 62_000, False),

    # ── Tashqi vositalar / Dermatologiya ──────────────────────────────────────
    ("Levomekol kremi 40g", "Левомеколь мазь 40г", "chloramphenicol+methyluracil",
     "Tashqi antibiotik/yara dori", "cream", "", "40g",
     ["levomekol", "lewomekol", "levomycetin"], 14_000, 28_000, False),

    ("Baneocin kremi 20g", "Банеоцин крем 20г", "neomycin+bacitracin",
     "Tashqi antibiotik", "cream", "", "20g",
     ["baneotsin", "baneocin"], 32_000, 62_000, False),

    ("Solcoseryl geli 20g", "Солкосерил гель 20г", "deproteinized hemodialysate",
     "Tashqi regenerant", "gel", "", "20g",
     ["solkoseryl", "solcoseryl"], 32_000, 62_000, False),

    ("Klotrimazol kremi 20g", "Клотримазол крем 20г", "clotrimazole",
     "Tashqi antifungal", "cream", "1%", "20g",
     ["klotrimazola", "canesten", "clotrimazole"], 10_000, 22_000, False),

    ("Triderm kremi 30g", "Тридерм крем 30г", "betamethasone+gentamicin+clotrimazole",
     "Tashqi kombinatsiyalangan", "cream", "", "30g",
     ["triderm", "betaderm"], 52_000, 100_000, True),

    ("Betadine 10% malhami 20g", "Бетадин 10% мазь 20г", "povidone-iodine",
     "Tashqi antiseptik", "ointment", "10%", "20g",
     ["betadin", "betadine", "povidon-iodin"], 28_000, 55_000, False),

    ("Vodorod peroksid 3% 100ml", "Перекись водорода 3% 100мл", "hydrogen peroxide",
     "Antiseptik", "solution", "3%", "100ml",
     ["h2o2", "peroksid", "perekis"], 3_000, 7_000, False),

    ("Zelyonka (brilliant yashil) 25ml", "Зелёнка 25мл", "brilliant green",
     "Antiseptik", "solution", "1%", "25ml",
     ["zelenka", "brilliant green"], 3_000, 8_000, False),

    ("Yod eritmasi 5% 25ml", "Йод раствор 5% 25мл", "iodine",
     "Antiseptik", "solution", "5%", "25ml",
     ["yod", "iodine solution"], 4_000, 10_000, False),

    ("Xloregeksidin 0.05% 100ml", "Хлоргексидин 0,05% 100мл", "chlorhexidine",
     "Antiseptik", "solution", "0.05%", "100ml",
     ["xloreksidin", "chlorhexidine", "corsodyl"], 4_000, 10_000, False),

    ("Miramistin 150ml", "Мирамистин 150мл", "miramistin",
     "Antiseptik/Antibakterial", "solution", "0.01%", "150ml",
     ["miramistin"], 32_000, 62_000, False),

    # ── Ko'z preparatlari ─────────────────────────────────────────────────────
    ("Albucid (Sulfatsetamid) 20% 10ml", "Альбуцид 20% 10мл", "sulfacetamide",
     "Ko'z tomchisi (antibiotik)", "eye drops", "20%", "10ml",
     ["albucid", "sulfatsetamid"], 6_000, 14_000, False),

    ("Tobramycin ko'z tomchisi 5ml", "Тобрамицин глазные капли 5мл", "tobramycin",
     "Ko'z tomchisi (antibiotik)", "eye drops", "0.3%", "5ml",
     ["tobramitsin", "tobrex", "tobradex"], 32_000, 62_000, True),

    ("Visine ko'z tomchisi 15ml", "Визин глазные капли 15мл", "tetryzoline",
     "Ko'z tomchisi (vazokonstriktor)", "eye drops", "0.05%", "15ml",
     ["visine", "tetrizolin"], 18_000, 38_000, False),

    ("Optive ko'z tomchisi 10ml", "Оптив глазные капли 10мл", "carboxymethylcellulose",
     "Ko'z tomchisi (namlovchi)", "eye drops", "", "10ml",
     ["optive", "hilo comod", "systane"], 42_000, 80_000, False),

    # ── Antiviral ─────────────────────────────────────────────────────────────
    ("Aciclovir 200mg №20", "Ацикловир 200мг №20", "aciclovir",
     "Antiviral (Gerpes)", "tablet", "200mg", "20 ta",
     ["atsiklovir", "zovirax", "acyclovir"], 14_000, 28_000, False),

    ("Aciclovir krem 5% 5g", "Ацикловир крем 5% 5г", "aciclovir",
     "Tashqi antiviral", "cream", "5%", "5g",
     ["atsiklovir krem", "zovirax krem"], 12_000, 25_000, False),

    ("Arbidol 100mg №20", "Арбидол 100мг №20", "umifenovir",
     "Antiviral/Immunomodulyator", "tablet", "100mg", "20 ta",
     ["arbidol", "umifenovir", "aflu"], 32_000, 62_000, False),

    ("Oscillococcinum №6", "Оциллококцинум №6", "oscillococcinum",
     "Antiviral (Gomeotopiya)", "granule", "", "6 ta doza",
     ["oscillococcinum", "osilococcinum"], 52_000, 100_000, False),

    # ── Qon bosimi dori (qo'shimcha) ──────────────────────────────────────────
    ("Amlodipine+Valsartan 5/80mg №30", "Амлодипин+Валсартан 5/80мг №30",
     "amlodipine+valsartan",
     "Kombinatsiyalangan gipertoniya dori", "tablet", "5mg+80mg", "30 ta",
     ["exforge", "vamloset"], 65_000, 125_000, True),

    ("Indapamid 2.5mg №30", "Индапамид 2,5мг №30", "indapamide",
     "Diuretik/Gipertoniya dori", "tablet", "2.5mg", "30 ta",
     ["indapamid", "arifon", "ionik"], 15_000, 32_000, True),

    ("Furosemid 40mg №50", "Фуросемид 40мг №50", "furosemide",
     "Diuretik", "tablet", "40mg", "50 ta",
     ["furosemid", "lasix"], 8_000, 18_000, True),

    ("Spironolakton 50mg №20", "Спиронолактон 50мг №20", "spironolactone",
     "Diuretik (kaliyni saqlovchi)", "tablet", "50mg", "20 ta",
     ["spironolakton", "veroshpiron", "aldactone"], 18_000, 38_000, True),

    # ── Yuqori nafas yo'llari/ORL ─────────────────────────────────────────────
    ("Tizin Xylo burun spreyi 0.1%", "Тизин Ксило спрей 0,1%", "xylometazoline",
     "Burun spreyi", "spray", "0.1%", "10ml",
     ["tizin", "xymelin", "xinosine"], 20_000, 40_000, False),

    ("Isofra burun spreyi", "Изофра назальный спрей", "framycetin",
     "Burun antibiotigi", "spray", "", "15ml",
     ["isofra", "framikatin"], 55_000, 105_000, True),

    ("Polydex burun spreyi", "Полидекса назальный спрей", "neomycin+polymyxin+dexamethasone",
     "Kombinatsiyalangan burun spreyi", "spray", "", "15ml",
     ["polydex", "polideksa"], 52_000, 100_000, True),

    ("Rinofluimucil burun spreyi", "Ринофлуимуцил спрей", "acetylcysteine+tuaminoheptane",
     "Burun spreyi (mukolitik)", "spray", "", "10ml",
     ["rinofluimucil", "rinofluimyusil"], 45_000, 88_000, False),

    # ── Suyak va bo'g'im ──────────────────────────────────────────────────────
    ("Artra №60", "Артра №60", "glucosamine+chondroitin",
     "Xondroprotektor", "tablet", "500mg+500mg", "60 ta",
     ["artra", "glyukozamin+xondroitin", "teraflex"], 85_000, 160_000, False),

    ("Teraflex №60", "Терафлекс №60", "glucosamine+chondroitin",
     "Xondroprotektor", "capsule", "500mg+400mg", "60 ta",
     ["teraflex", "dona", "xondroitin"], 90_000, 170_000, False),

    ("Voltaren Emulgel 1% 50g", "Вольтарен Эмульгель 1% 50г", "diclofenac",
     "Tashqi NSAID", "gel", "1%", "50g",
     ["voltaren gel", "diklofenac gel", "ortofen gel"], 42_000, 80_000, False),

    ("Fastum gel 2.5% 50g", "Фастум гель 2,5% 50г", "ketoprofen",
     "Tashqi NSAID", "gel", "2.5%", "50g",
     ["fastum", "ketoprofen gel"], 45_000, 88_000, False),

    # ── Jinsiy salomatlik / Kontraseptivlar ───────────────────────────────────
    ("Yarina №21", "Ярина №21", "drospirenone+ethinylestradiol",
     "Oral kontraseptiv", "tablet", "3mg+0.03mg", "21 ta",
     ["yarina", "yariva"], 82_000, 150_000, True),

    ("Regulon №21", "Регулон №21", "desogestrel+ethinylestradiol",
     "Oral kontraseptiv", "tablet", "0.15mg+0.03mg", "21 ta",
     ["regulon", "marvelon"], 42_000, 85_000, True),

    ("Postinor №2", "Постинор №2", "levonorgestrel",
     "Favqulodda kontraseptiv", "tablet", "750mcg", "2 ta",
     ["postinor", "norlevo", "escapelle"], 32_000, 62_000, False),

    # ── Siydik yo'llari / Prostat ─────────────────────────────────────────────
    ("Tamsulosin 0.4mg №30", "Тамсулозин 0,4мг №30", "tamsulosin",
     "Prostat dori (alfa-bloker)", "capsule", "0.4mg", "30 ta",
     ["tamsulosin", "omnic", "focusin"], 38_000, 78_000, True),

    ("Kanefron N №60", "Канефрон Н №60", "herbal combination",
     "Siydik yo'llari fitopreparati", "tablet", "", "60 ta",
     ["kanefron", "canephron"], 32_000, 62_000, False),

    ("Tsiston №100", "Цистон №100", "herbal combination",
     "Siydik yo'llari fitopreparati", "tablet", "", "100 ta",
     ["tsiston", "cystone"], 22_000, 45_000, False),

    ("Fitolisin pasta 100g", "Фитолизин паста 100г", "herbal combination",
     "Siydik yo'llari fitopreparati", "paste", "", "100g",
     ["fitolysin", "phytolysin"], 28_000, 55_000, False),

    # ── Qo'shimcha / Keng qo'llaniladigan ────────────────────────────────────
    ("Deksametazon 4mg №10 amp", "Дексаметазон 4мг №10 амп", "dexamethasone",
     "Kortikosteroid", "injection", "4mg/ml", "10 ta ampula",
     ["deksamatazon", "dexamethasone", "fortecortin"], 18_000, 38_000, True),

    ("Prednizolon 5mg №40", "Преднизолон 5мг №40", "prednisolone",
     "Kortikosteroid", "tablet", "5mg", "40 ta",
     ["prednizolon", "prednisolone"], 12_000, 26_000, True),

    ("Suprastineks №7", "Супрастинекс №7", "levocetirizine",
     "Antigistamin (3-avlod)", "tablet", "5mg", "7 ta",
     ["suprastineks", "levocetirizin", "xyzal"], 28_000, 55_000, False),

    ("Enterofuril 200mg №16", "Энтерофурил 200мг №16", "nifuroxazide",
     "Ichak antiseptigi", "capsule", "200mg", "16 ta",
     ["enterofuril", "nifuroksazid", "stopdiare"], 38_000, 72_000, False),

    ("Nifuroksazid 200mg №20", "Нифуроксазид 200мг №20", "nifuroxazide",
     "Ichak antiseptigi", "tablet", "200mg", "20 ta",
     ["nifuroksazid", "enterofuril generik"], 18_000, 38_000, False),

    ("Tanakan 40mg №90", "Танакан 40мг №90", "ginkgo biloba",
     "Nootropik (fitovosita)", "tablet", "40mg", "90 ta",
     ["tanakan", "ginkgo biloba", "ginkgo forte"], 52_000, 100_000, False),

    ("Actovegin 200mg №50", "Актовегин 200мг №50", "deproteinized hemodialysate",
     "Neyroprotektiv/Metabolik", "tablet", "200mg", "50 ta",
     ["aktovegin", "actovegin"], 85_000, 160_000, True),

    ("Cerebrolysin №10 amp", "Церебролизин №10 амп", "porcine brain hydrolysate",
     "Neyroprotektiv", "injection", "1ml", "10 ta ampula",
     ["tserebrolisin", "cerebrolysin"], 55_000, 110_000, True),
]


async def run():
    db = await get_db()
    await create_indexes(db)

    # ── 1. Yangi dorilarni qo'shish ───────────────────────────────────────────
    existing_generics = set()
    async for med in db[MEDICINES].find({}, {"generic_name": 1, "dosage": 1, "pack_size": 1}):
        key = f"{med.get('generic_name','')}|{med.get('dosage','default')}|{med.get('pack_size','')}"
        existing_generics.add(key)

    new_meds = []
    for row in MEDICINES_DATA:
        (name_uz, name_ru, generic_name, category, dosage_form,
         dosage, pack_size, synonyms, price_min, price_max, rx) = row

        key = f"{generic_name}|{dosage or 'default'}|{pack_size}"
        if key in existing_generics:
            continue

        new_meds.append({
            "name_uz": name_uz,
            "name_ru": name_ru,
            "generic_name": generic_name,
            "category": category,
            "dosage_form": dosage_form,
            "dosage": dosage,
            "pack_size": pack_size,
            "synonyms": synonyms,
            "price_min": price_min,
            "price_max": price_max,
            "requires_prescription": rx,
        })
        existing_generics.add(key)

    if new_meds:
        result = await db[MEDICINES].insert_many(new_meds)
        logger.success(f"{len(result.inserted_ids)} ta yangi dori qo'shildi")
    else:
        logger.info("Barcha dorilar allaqachon mavjud")

    # ── 2. Barcha dorlarni narq diapazoni bilan yuklaymiz ─────────────────────
    all_meds = await db[MEDICINES].find(
        {}, {"_id": 1, "price_min": 1, "price_max": 1, "generic_name": 1}
    ).to_list(None)

    if not all_meds:
        logger.error("Dorilar topilmadi!")
        return

    # Legacy dorlar (price_min/max yo'q bo'lsa) uchun standart diapazon
    def get_range(med: dict) -> tuple[int, int]:
        mn = med.get("price_min")
        mx = med.get("price_max")
        if mn and mx:
            return mn, mx
        # Eski dorilar uchun o'rtacha diapazon
        return 10_000, 40_000

    logger.info(f"Jami {len(all_meds)} ta dori mavjud")

    # ── 3. Haqiqiy dorixonalar inventarini yangilaymiz ────────────────────────
    ph_cursor = db[PHARMACIES].find(
        {"osm_id": {"$exists": True}},
        {"_id": 1}
    )
    ph_ids = [doc["_id"] async for doc in ph_cursor]
    logger.info(f"{len(ph_ids)} ta haqiqiy dorixona uchun inventar yangilanmoqda...")

    BATCH = 2000
    total_inv = 0
    random.seed(42)

    for i in range(0, len(ph_ids), 50):
        chunk = ph_ids[i:i + 50]
        if not chunk:
            break

        # Bu dorixonalar uchun eski inventarni o'chirish
        await db[INVENTORY].delete_many({"pharmacy_id": {"$in": chunk}})

        docs = []
        for ph_id in chunk:
            # Har bir dorixona dorlarning 40-75% ini sotadi
            k = random.randint(int(len(all_meds) * 0.40), int(len(all_meds) * 0.75))
            selected = random.sample(all_meds, k=k)

            for med in selected:
                mn, mx = get_range(med)
                # Dorixona narxi: diapazon ichida ±5% variant
                price = random.randint(mn, mx)
                # Ba'zi dorilar vaqtincha tugab qolgan bo'lishi mumkin (5%)
                in_stock = random.random() > 0.05
                docs.append({
                    "pharmacy_id": ph_id,
                    "medicine_id": med["_id"],
                    "price": price,
                    "in_stock": in_stock,
                    "updated_at": datetime.now(timezone.utc),
                })

        # Batch insert
        for j in range(0, len(docs), BATCH):
            batch = docs[j:j + BATCH]
            if batch:
                await db[INVENTORY].insert_many(batch, ordered=False)
                total_inv += len(batch)

        if (i // 50) % 5 == 0:
            logger.info(f"  {min(i + 50, len(ph_ids))}/{len(ph_ids)} dorixona, {total_inv:,} inventar yozuvi")

    # ── 4. Demo dorixonalar (10 ta eski) narxini ham yangilaymiz ─────────────
    demo_ids = [doc["_id"] async for doc in db[PHARMACIES].find(
        {"osm_id": {"$exists": False}}, {"_id": 1}
    )]

    if demo_ids:
        await db[INVENTORY].delete_many({"pharmacy_id": {"$in": demo_ids}})
        docs = []
        for ph_id in demo_ids:
            for med in all_meds:
                mn, mx = get_range(med)
                price = random.randint(mn, mx)
                docs.append({
                    "pharmacy_id": ph_id,
                    "medicine_id": med["_id"],
                    "price": price,
                    "in_stock": True,
                    "updated_at": datetime.now(timezone.utc),
                })
        if docs:
            await db[INVENTORY].insert_many(docs, ordered=False)
            total_inv += len(docs)
        logger.info(f"{len(demo_ids)} ta demo dorixona inventari yangilandi")

    final_med = await db[MEDICINES].count_documents({})
    final_inv = await db[INVENTORY].count_documents({})
    final_ph = await db[PHARMACIES].count_documents({})

    logger.success(
        f"\n{'='*50}\n"
        f"  NATIJA:\n"
        f"  Dorixonalar : {final_ph:,} ta\n"
        f"  Dorilar     : {final_med:,} ta\n"
        f"  Inventar    : {final_inv:,} ta yozuv\n"
        f"{'='*50}"
    )
    await close_db()


if __name__ == "__main__":
    asyncio.run(run())
