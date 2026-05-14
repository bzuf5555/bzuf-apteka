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
    user          = callback.from_user
    medicine_id_s = callback.data.split(":", 1)[1]

    try:
        medicine_id = ObjectId(medicine_id_s)
    except Exception:
        await callback.answer("Xato yuz berdi.", show_alert=True)
        return

    db_user = await queries.get_user(user.id)
    if not db_user or not db_user.get("lat"):
        await callback.answer("📍 Avval lokatsiyangizni ulashing!", show_alert=True)
        return

    med           = await queries.get_medicine_by_id(medicine_id)
    medicine_name = med.get("name_uz", "Dori") if med else "Dori"

    current_min = await queries.get_current_min_price(
        medicine_id, db_user["lat"], db_user["lng"]
    )
    if current_min is None:
        current_min = 0

    is_new = await queries.subscribe_price_watch(
        telegram_id      = user.id,
        medicine_id      = medicine_id,
        medicine_name    = medicine_name,
        user_lat         = db_user["lat"],
        user_lng         = db_user["lng"],
        current_min_price= current_min,
    )

    if is_new:
        await callback.message.edit_reply_markup(
            reply_markup=search_with_watch_kb(medicine_id_s, is_watching=True)
        )
        price_s = f"~{int(current_min):,} so'm" if current_min else "noma'lum"
        await callback.message.answer(
            f"🔔 <b>Narq kuzatuvi yoqildi!</b>\n\n"
            f"💊 {medicine_name}\n"
            f"💰 Hozirgi narx: <b>{price_s}</b>\n\n"
            f"Narq <b>15%</b> va undan ko'p tushganda xabar beraman.",
            parse_mode="HTML",
        )
        logger.info(f"Watch: {user.id} → {medicine_name}")
    else:
        await callback.answer("✅ Allaqachon kuzatuvdasiz!", show_alert=False)


@router.callback_query(F.data.startswith("unwatch:"))
async def cb_unwatch(callback: CallbackQuery) -> None:
    await callback.answer()
    medicine_id_s = callback.data.split(":", 1)[1]
    try:
        await queries.unsubscribe_price_watch(
            callback.from_user.id, ObjectId(medicine_id_s)
        )
    except Exception:
        pass
    await callback.message.edit_reply_markup(
        reply_markup=search_with_watch_kb(medicine_id_s, is_watching=False)
    )
    await callback.answer("🔕 Kuzatuvdan chiqildi.", show_alert=False)
