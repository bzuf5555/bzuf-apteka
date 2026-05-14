from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from bot.database import queries

router = Router()

STARS = {1: "⭐", 2: "⭐⭐", 3: "⭐⭐⭐", 4: "⭐⭐⭐⭐", 5: "⭐⭐⭐⭐⭐"}


@router.callback_query(F.data.startswith("rate:"))
async def cb_rate(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    _, ph_id_str, rating_str = parts
    try:
        rating = int(rating_str)
    except ValueError:
        return

    await queries.save_rating(callback.from_user.id, ph_id_str, rating)

    avg, count = await queries.get_pharmacy_avg_rating(ph_id_str)
    stars_text = STARS.get(rating, "⭐" * rating)
    await callback.message.answer(
        f"{stars_text} Bahoingiz saqlandi!\n"
        f"Ushbu dorixona o'rtacha: <b>{avg}⭐</b> ({count} ta baho)",
        parse_mode="HTML",
    )
    logger.info(f"Reyting: {callback.from_user.id} → {ph_id_str} = {rating}")
