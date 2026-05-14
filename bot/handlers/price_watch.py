"""
Narq kuzatuvi handlerlari.
Foydalanuvchi "🔔 Narq tushsa xabar ber" tugmasini bosganda ishga tushadi.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from bson import ObjectId
from loguru import logger

from bot.database import queries
from bot.keyboards.inline import search_with_watch_kb

router = Router()


@router.callback_query(F.data.startswith("watch:"))
async def cb_watch(callback: CallbackQuery) -> None:
    await callback.answer()
    user = callback.from_user
    medicine_id_str = callback.data.split(":", 1)[1]

    try:
        medicine_id = ObjectId(medicine_id_str)
    except Exception:
        await callback.answer("Xato yuz berdi.", show_alert=True)
        return

    db_user = await queries.get_user(user.id)
    if not db_user or not db_user.get("lat"):
        await callback.answer("Avval lokatsiyangizni ulashing!", show_alert=True)
        return

    # Dori nomini olish
    med = await queries.get_medicine_by_id(medicine_id)
    medicine_name = med.get("name_uz", "Dori") if med else "Dori"

    # Hozirgi eng arzon narqni olish
    current_min = await queries.get_current_min_price(
        medicine_id, db_user["lat"], db_user["lng"]
    )
    if current_min is None:
        await callback.answer(
            "Hozir atrofingizda bu dori topilmadi, lekin kuzatuvga qo'shildi.",
            show_alert=False,
        )
        current_min = 0

    is_new = await queries.subscribe_price_watch(
        telegram_id=user.id,
        medicine_id=medicine_id,
        medicine_name=medicine_name,
        user_lat=db_user["lat"],
        user_lng=db_user["lng"],
        current_min_price=current_min,
    )

    if is_new:
        await callback.message.edit_reply_markup(
            reply_markup=search_with_watch_kb(medicine_id_str, is_watching=True)
        )
        price_text = f"{int(current_min):,} so'm" if current_min > 0 else "nomaʼlum"
        await callback.message.answer(
            f"🔔 <b>{medicine_name}</b> narqi kuzatuvga qo'shildi!\n\n"
            f"Hozirgi eng arzon narq: <b>{price_text}</b>\n"
            f"Narq <b>15% va undan ko'p</b> tushganda xabar beraman.",
            parse_mode="HTML",
        )
        logger.info(f"Watch qo'shildi: {user.id} → {medicine_name} @ {current_min}")
    else:
        await callback.answer("Allaqachon kuzatuvdasiz! ✅", show_alert=False)


@router.callback_query(F.data.startswith("unwatch:"))
async def cb_unwatch(callback: CallbackQuery) -> None:
    await callback.answer()
    medicine_id_str = callback.data.split(":", 1)[1]

    try:
        medicine_id = ObjectId(medicine_id_str)
    except Exception:
        return

    await queries.unsubscribe_price_watch(callback.from_user.id, medicine_id)
    await callback.message.edit_reply_markup(
        reply_markup=search_with_watch_kb(medicine_id_str, is_watching=False)
    )
    await callback.answer("🔕 Kuzatuvdan chiqildi.", show_alert=False)
    logger.info(f"Watch bekor: {callback.from_user.id} → {medicine_id_str}")
