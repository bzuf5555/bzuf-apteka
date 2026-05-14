# Dorixona Qidiruv Bot — Claude Qoidalari

## Loyiha Haqida
O'zbekistondagi dorixonalarda dori mavjudligi, narxi va manzilini ko'rsatuvchi Telegram bot.
Foydalanuvchi "Menga Paracetamol kerak" deb yozadi → bot yaqin-atrofdagi dorixonalarni ko'rsatadi.

## Stack
- **Bot**: aiogram 3.x (async)
- **DB**: MongoDB Atlas (bepul, motor async driver)
- **Geo**: MongoDB 2dsphere + $near (ST_DWithin ekvivalenti)
- **Deploy**: Render.com (bepul web service, webhook mode)
- **AI**: Anthropic Claude (token-saver orqali)

## Asosiy Qoidalar

### 1. Task Tracking (MAJBURIY)
- Har qanday ish boshlashdan oldin `task.md` ni tekshir
- Ish tugatilgandan DARHOL `done.md` ga ko'chir
- `task.md` da: PENDING va IN_PROGRESS tasklar
- `done.md` da: tugallangan tasklar (sana bilan)

### 2. Zero Cost Qoidasi
- Hech qanday pullik servis ISHLATILMAYDI
- Free tier: SQLite, Supabase free, Railway free, Render free
- Claude API: token-saver agent orqali tejamkorlik bilan ishlatiladi

### 3. Bot Qoidalari (Ikki bosqichli ro'yxatdan o'tish)
- `/start` → **1-qadam**: kontakt (telefon raqam) MAJBURIY
- Kontakt keyin → **2-qadam**: lokatsiya MAJBURIY
- Har ikkisi bo'lmasa → bot qidiruv xizmati ishlamaydi
- Boshqa odamning kontakti qabul qilinmaydi
- Barcha xabarlar O'zbek tilida (qisqa, aniq)

### 4. Token-Saver Agent Qoidasi
Claude API chaqiruvlarida DOIM `token_saver` orqali o'tkaziladi:
```
Haiku  → Oddiy: tarjima, normalizatsiya, qisqa lookup (< 200 token kutilsa)
Sonnet → O'rta: qidiruv, tahlil, formatting (200-800 token)
Opus   → Murakkab: chuqur tahlil, arxitektura qarorlari (800+ token)
```

### 5. Kod Qoidalari
- Python 3.11+, to'liq async (asyncio + aiogram 3.x)
- Barcha DB so'rovlari async (aiosqlite)
- Type hints — har doim
- Xatoliklar foydalanuvchiga O'zbekcha, consolega inglizcha
- Geo hisoblash: Haversine (SQLite), ST_DWithin (Supabase)
- Dori nomlari: fuzzy match (rapidfuzz) + Claude NLP

### 6. Arxitektura Qoidalari
```
bot/
├── handlers/     # Telegram voqealarini qabul qiladi
├── services/     # Biznes mantiq
├── agents/       # Claude-based agentlar (token_saver, nlp, search)
├── database/     # Modellar, connection, querylar
└── keyboards/    # Reply va Inline klaviaturalar
```

### 7. Multi-Agent Qoidasi
- `token_saver.py` — barcha Claude chaqiruvlarni yo'naltiradi
- `nlp_agent.py` — dori nomlarini normallashtiradi
- `search_agent.py` — qidiruv natijalarini tahlil qiladi
- Agentlar o'rtasida ma'lumot JSON formatida uzatiladi

### 8. MongoDB Sxemasi
```
users        → telegram_id, phone, username, full_name, lat, lng, registered_at
pharmacies   → name, address, location (GeoJSON Point), phone, hours, is_active
medicines    → name_uz, name_ru, generic_name, category, synonyms[]
inventory    → pharmacy_id (ObjectId), medicine_id (ObjectId), price, in_stock
search_log   → telegram_id, query, results_count, searched_at
```
- `pharmacies.location` → 2dsphere index (geo qidiruv uchun)
- Geo qidiruv: `$near + $maxDistance` (metrda)
- ObjectId lar DOIM `bson.ObjectId` sifatida saqlash

### 9. Xavfsizlik
- `.env` faylida BARCHA sirlar (token, key) — hech qachon koda emas
- SQL injection: parametrlashtirilgan so'rovlar FAQAT
- Rate limiting: foydalanuvchi boshiga minutiga maks 10 so'rov

### 10. Sifat Standarti
Kod sifati senior dasturchidan YUQORI bo'lishi shart:
- Har bir function bitta mas'uliyat (SRP)
- Edge case'lar hisobga olinadi (bo'sh natija, tarmoq xatosi, noto'g'ri input)
- Logging: barcha muhim voqealar log'lanadi
