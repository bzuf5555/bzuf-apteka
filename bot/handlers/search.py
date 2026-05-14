from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from loguru import logger

from bot.database import queries
from bot.services import search_service
from bot.keyboards.reply import location_request_kb, main_menu_kb
from bot.keyboards.inline import search_again_kb

router = Router()

NO_LOCATION_MSG = """⚠️ <b>Lokatsiya topilmadi!</b>

Dorixonalarni topish uchun joylashuvingizni ulashing.
Quyidagi tugmani bosing 👇"""

SEARCHING_MSG = "🔍 Qidirilmoqda..."

MIN_QUERY_LEN = 2
MAX_QUERY_LEN = 100


@router.message(F.text == "🔍 Dori qidirish")
async def prompt_search(message: Message) -> None:
    user = message.from_user
    has_location = await queries.user_has_location(user.id)
    if not has_location:
        await message.answer(NO_LOCATION_MSG, reply_markup=location_request_kb(), parse_mode="HTML")
        return
    await message.answer("💊 Qaysi dorini qidiryapsiz? Dori nomini yozing:")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_medicine_query(message: Message) -> None:
    user = message.from_user
    text = (message.text or "").strip()

    if text in {"ℹ️ Yordam", "🔍 Dori qidirish"}:
        return

    if len(text) < MIN_QUERY_LEN:
        await message.answer("❓ Dori nomini to'liqroq yozing (kamida 2 ta harf).")
        return

    if len(text) > MAX_QUERY_LEN:
        await message.answer("❓ Juda uzun so'rov. Faqat dori nomini yozing.")
        return

    db_user = await queries.get_user(user.id)
    if not db_user or not db_user.get("lat"):
        await message.answer(
            NO_LOCATION_MSG,
            reply_markup=location_request_kb(),
            parse_mode="HTML",
        )
        return

    searching_msg = await message.answer(SEARCHING_MSG)

    try:
        result = await search_service.search_medicine(
            user_query=text,
            user_lat=db_user["lat"],
            user_lng=db_user["lng"],
            telegram_id=user.id,
        )
        await searching_msg.delete()
        await message.answer(result, parse_mode="HTML", reply_markup=search_again_kb())
    except Exception as e:
        logger.error(f"Qidiruv xatosi [{user.id}]: {e}")
        await searching_msg.delete()
        await message.answer(
            "⚠️ Qidiruv amalga oshmadi. Iltimos, qayta urinib ko'ring.",
            reply_markup=main_menu_kb(),
        )


@router.callback_query(F.data == "search_again")
async def cb_search_again(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("💊 Qaysi dorini qidiryapsiz? Dori nomini yozing:")


@router.callback_query(F.data == "update_location")
async def cb_update_location(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "📍 Yangi lokatsiyangizni ulashing:",
        reply_markup=location_request_kb(),
    )
