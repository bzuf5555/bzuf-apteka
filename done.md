



# Done.md — Tugallangan Ishlar

## 2026-05-14

### Phase 0: Tahlil va Arxitektura
- [x] Loyiha chuqur tahlili
- [x] `CLAUDE.md` — 10 ta qoida + MongoDB/Render stack
- [x] Memory fayllar yaratildi

### Phase 1: Foundation
- [x] `requirements.txt` — motor, pymongo, aiosqlite O'CHIRILDI
- [x] `.env.example` — MONGODB_URI, WEBHOOK_HOST, WEBHOOK_SECRET qo'shildi
- [x] `.gitignore`
- [x] `bot/config.py` — MONGODB_URI, webhook_path, webhook_url xususiyatlari

### Phase 2: MongoDB Layer
- [x] `bot/database/connection.py` — Motor AsyncIOMotorClient
- [x] `bot/database/models.py` — kolleksiya nomlari + 2dsphere index yaratish
- [x] `bot/database/queries.py` — to'liq MongoDB qayta yozildi:
  - upsert/get user, save_user_contact, user_has_contact
  - MongoDB $near geo qidiruv (2dsphere)
  - inventory join + price_map
  - search_log, get_stats

### Phase 3: Services (MongoDB uchun yangilandi)
- [x] `bot/services/pharmacy_service.py` — GeoJSON Point, Motor insert
- [x] `bot/services/search_service.py` — ObjectId bilan qidiruv
- [x] `bot/services/geo_service.py` — Haversine (fallback uchun saqlab qolindi)

### Phase 4: Bot (Ikki bosqichli flow)
- [x] `bot/keyboards/reply.py` — contact_request_kb() qo'shildi
- [x] `bot/handlers/contact.py` — YANGI: telefon qabul qilish, o'z kontakti tekshiruvi
- [x] `bot/handlers/start.py` — 3 holat: yangi→kontakt | kontaktsiz→lokatsiya | to'liq→menyu
- [x] `bot/handlers/location.py` — kontaktsiz lokatsiya qabul qilinmaydi
- [x] `bot/handlers/search.py` — o'zgarmadi
- [x] `bot/handlers/admin.py` — MongoDB count_documents

### Phase 5: Entry Point + Deploy
- [x] `bot/main.py` — polling (dev) / webhook (production Render) ikki rejim
  - aiohttp server, /health endpoint
  - BOT_ENV=production + WEBHOOK_HOST → webhook
- [x] `Procfile` — `web: python -m bot.main`
- [x] `render.yaml` — Render deploy konfiguratsiyasi
- [x] `runtime.txt` — Python 3.11.9

### Phase 6: O'rnatish va Tekshirish
- [x] Python 3.11.9 venv yaratildi (`.venv/`)
- [x] `requirements.txt` versiya ziddiyatlari hal qilindi (compatible release `~=`)
- [x] `pip install` muvaffaqiyatli: aiogram 3.28.2, motor 3.7.1, pymongo 4.17.0 o'rnatildi
- [x] 24 ta Python fayl sintaksis tekshiruvi — xato yo'q
- [x] Webhook import tekshiruvi — OK
- [x] `.env` fayli `.env.example` dan yaratildi

### Phase 8: Ishga tushirish
- [x] MongoDB 8.3 o'rnatildi (winget) → `C:\Program Files\MongoDB\Server\8.3\`
- [x] `mongod` ishga tushirildi (`C:\data\db` data dir)
- [x] `scripts/seed_data.py` — 10 dorixona, 15 dori, 106 inventar MongoDB ga yozildi
- [x] `git init` + initial commit (35 fayl, 1569 qator)
- [x] GitHub push → `https://github.com/bzuf5555/bzuf-apteka.git`
- [x] Bot ishga tushirildi → `@bzuf_apteka_bot` polling mode ✅
- [x] aiogram 3.28 startup handler xatosi tuzatildi va push qilindi

### Phase 9: MongoDB Atlas + Render Deploy (Playwright + API)
- [x] MongoDB Atlas — Playwright orqali avtomatik ulandi
- [x] `bzuf5555_db_user` paroli yangilandi (autogenerate)
- [x] Network Access `0.0.0.0/0` — allaqachon sozlangan
- [x] MongoDB Atlas ga seed: 10 dorixona, 15 dori, 106 inventar
- [x] Render API key yaratildi: `dorixona-bot`
- [x] Render Web Service yaratildi: `dorixona-bot` → `https://dorixona-bot-b48s.onrender.com`
- [x] 9 ta env var Render ga o'rnatildi (BOT_TOKEN, MONGODB_URI, WEBHOOK_HOST, va h.k.)
- [x] Deploy boshlandi → 2 xato tuzatildi (Python 3.11, AppRunner) → **`live`** ✅
- [x] Telegram webhook: `https://dorixona-bot-b48s.onrender.com/bot/...` — faol
- [x] `/start` xulq-atvor o'zgartirildi: qaytgan foydalanuvchi → faqat lokatsiya so'raladi (kontaktsiz)
- [x] Haqiqiy Toshkent dorixonalari: 991 ta OSM dorixona → MongoDB, jami 1001 ta
- [x] **171 ta haqiqiy dori** (oldin 15 ta edi) — UZS narq diapazoni bilan:
  - Analgetiklar, antibiotiklar, kardiovaskulyar, oshqozon, nafas yo'llari, vitaminlar, diabet, asab, dermatologiya, ko'z, antiviral va boshqalar
  - Har bir dori: price_min, price_max (haqiqiy O'zbekiston bozori narxlari 2024-2025)
  - 98,530 ta inventar yozuvi (1001 dorixona × ~98 ta dori)
- [x] **Narx diapazoni ko'rinishi**: "9,000–11,000 so'm (taxminiy)" — foydalanuvchi aldanmaydi
- [x] **146 ta dori rasmi** Wikipedia Wikimedia Commons dan (171 dan 85% coverage)
- [x] **Narq tushganda ogohlantirish (push notification)**:
  - Qidiruv natijasida "🔔 Narq tushsa xabar ber" tugmasi
  - `price_watches` kolleksiyasi (user + medicine + kuzatuv narxi)
  - Fon vazifasi har 6 soatda tekshiradi (asyncio.create_task)
  - Narq ≥15% tushsa → foydalanuvchiga Telegram xabari
  - Bot avval dorining rasmini yuboradi → foydalanuvchi aniq dorini ko'radi
  - So'ng dorixonalar ro'yxati yuboriladi
- [x] UptimeRobot monitor: `/health` ni kuzatmoqda (bot uyquga ketmasligi uchun)

### Phase 10: Scripts
- [x] `scripts/migrate.py` — MongoDB 2dsphere index yaratish
- [x] `scripts/seed_data.py` — idempotent, 10 dorixona + 15 dori + inventar
