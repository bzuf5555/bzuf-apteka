"""
Dorixona lokatsiya callback handleri.
Foydalanuvchi "📍N. Dorixona nomi" tugmasini bosganda
dorixonaning native Telegram lokatsiya xabarini yuboradi.
Foydalanuvchi uni Google Maps / Yandex Maps / 2GIS da ochishi mumkin.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bson import ObjectId
from loguru import logger

from bot.database.connection import get_db
from bot.database.models import PHARMACIES

router = Router()


@router.callback_query(F.data.startswith("loc:"))
async def cb_send_pharmacy_location(callback: CallbackQuery) -> None:
    await callback.answer()

    ph_id_str = callback.data.split(":", 1)[1]
    try:
        ph_id = ObjectId(ph_id_str)
    except Exception:
        await callback.answer("Lokatsiya topilmadi.", show_alert=True)
        return

    db = await get_db()
    ph = await db[PHARMACIES].find_one(
        {"_id": ph_id},
        {"name": 1, "address": 1, "location": 1, "phone": 1, "working_hours": 1},
    )

    if not ph or not ph.get("location"):
        await callback.answer("Bu dorixonaning lokatsiyasi mavjud emas.", show_alert=True)
        return

    coords = ph["location"]["coordinates"]
    lng, lat = coords[0], coords[1]
    name    = ph.get("name", "Dorixona")
    address = ph.get("address", "")
    phone   = ph.get("phone", "")
    hours   = ph.get("working_hours", "")

    # Native Telegram lokatsiya — Google Maps / Yandex / 2GIS da ochiladi
    await callback.message.answer_location(
        latitude=lat,
        longitude=lng,
    )

    # Qisqacha ma'lumot
    info = f"📍 <b>{name}</b>"
    if address:
        info += f"\n🏠 {address}"
    if hours:
        info += f"\n🕐 {hours}"
    if phone:
        info += f"\n📞 {phone}"
    info += "\n\n<i>Xaritani ochish uchun yuqoridagi lokatsiyaga bosing 👆</i>"

    await callback.message.answer(info, parse_mode="HTML")
    logger.info(f"Lokatsiya yuborildi: {callback.from_user.id} → {name}")
