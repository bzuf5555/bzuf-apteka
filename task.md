# Task.md — Dorixona Qidiruv Bot

## IN_PROGRESS
_(hozircha yo'q)_

## PENDING

### Ishga tushirish (lokal test)
- [x] `.env` faylini yaratish — yaratildi
- [x] `pip install -r requirements.txt` — muvaffaqiyatli (Python 3.11 venv)
- [x] Kod sintaksis tekshiruvi — 24 fayl, xato yo'q
- [ ] `.env` ga BOT_TOKEN va MONGODB_URI kiritish (foydalanuvchi)
- [ ] `python scripts/seed_data.py` — demo ma'lumot qo'shish
- [ ] `python -m bot.main` — botni ishga tushirish va test qilish

### Render Deploy
- [ ] GitHub repo yaratish va loyihani push qilish
- [ ] https://render.com → New Web Service → GitHub repo ulash
- [ ] Environment variables qo'shish:
  - `BOT_TOKEN`, `MONGODB_URI`, `ANTHROPIC_API_KEY`
  - `WEBHOOK_HOST` = `https://your-app.onrender.com`
  - `WEBHOOK_SECRET` = tasodifiy string
  - `BOT_ENV` = `production`
- [ ] Deploy tugagandan keyin webhook URL ni tekshirish:
  `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### Kelajak (Phase 7)
- [ ] Dorixona admin panel (inventar yangilash uchun)
- [ ] Ko'p til (rus tili qo'shish)
- [ ] Dori narxi o'zgarganda ogohlantirish
- [ ] UptimeRobot bilan Render free tier uyg'otib turish (ping /health)
- [ ] Supabase geo yoki Atlas Search (full-text qidiruv)
