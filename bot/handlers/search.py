from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from loguru import logger

from bot.database import queries
from bot.services import search_service
from bot.agents.search_agent import format_generic_alternatives
from bot.keyboards.reply import location_request_kb, main_menu_kb
from bot.keyboards.inline import (
    search_again_kb, search_with_watch_kb, symptom_medicines_kb
)

router = Router()

NO_LOCATION_MSG = "⚠️ <b>Lokatsiya topilmadi!</b>\n\nDorixonalarni topish uchun joylashuvingizni ulashing 👇"
SEARCHING_MSG = "🔍 Qidirilmoqda..."
MIN_QUERY_LEN = 2
MAX_QUERY_LEN = 100


@router.message(F.text == "🔍 Dori qidirish")
async def prompt_search(message: Message) -> None:
    if not await queries.user_has_location(message.from_user.id):
        await message.answer(NO_LOCATION_MSG, reply_markup=location_request_kb(), parse_mode="HTML")
        return
    await message.answer("💊 Qaysi dorini qidiryapsiz? Dori nomini yozing:")


@router.message(F.text & ~F.text.startswith("/"))
async def handle_medicine_query(message: Message) -> None:
    user = message.from_user
    text = (message.text or "").strip()

    if text in {"ℹ️ Yordam", "🔍 Dori qidirish", "⭐ Mening dorilarim"}:
        return
    if len(text) < MIN_QUERY_LEN:
        await message.answer("❓ Kamida 2 ta harf yozing.")
        return
    if len(text) > MAX_QUERY_LEN:
        await message.answer("❓ Faqat dori yoki alomat nomini yozing.")
        return

    db_user = await queries.get_user(user.id)
    if not db_user or not db_user.get("lat"):
        await message.answer(NO_LOCATION_MSG, reply_markup=location_request_kb(), parse_mode="HTML")
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

        # Alomat aniqlanganida
        if result.get("is_symptom"):
            medicines = result.get("symptom_medicines", [])
            advice = result.get("symptom_advice", "")
            med_list = "\n".join(f"• <i>{m.capitalize()}</i>" for m in medicines)
            await message.answer(
                f"🩺 <b>Alomat bo'yicha tavsiya:</b>\n\n"
                f"{advice}\n\n"
                f"<b>Mos dorilar:</b>\n{med_list}\n\n"
                f"Qaysi birini qidirishni xohlaysiz?",
                reply_markup=symptom_medicines_kb(medicines),
                parse_mode="HTML",
            )
            return

        # Dori topilmadi
        if not result.get("found"):
            await message.answer(result["text"], parse_mode="HTML", reply_markup=search_again_kb())
            return

        # Rasm
        if result.get("image_url"):
            try:
                from aiogram.types import URLInputFile
                await message.answer_photo(
                    photo=URLInputFile(result["image_url"]),
                    caption=f"💊 <b>{result['display_name']}</b>",
                    parse_mode="HTML",
                )
            except Exception:
                pass

        # Generic muqobil bo'limi
        alt_text = format_generic_alternatives(
            result.get("generic_alternatives", []), result["display_name"]
        )
        full_text = result["text"] + alt_text if alt_text else result["text"]

        # Narq kuzatuvi + saqlash tugmasi
        mid = result.get("medicine_id")
        is_saved = await queries.is_medicine_saved(user.id, __import__("bson").ObjectId(mid)) if mid else False
        kb = search_with_watch_kb(mid, is_saved=is_saved) if mid else search_again_kb()

        await message.answer(full_text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.error(f"Qidiruv xatosi [{user.id}]: {e}")
        await searching_msg.delete()
        await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko'ring.", reply_markup=main_menu_kb())


@router.callback_query(F.data == "search_again")
async def cb_search_again(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("💊 Qaysi dorini qidiryapsiz?")


@router.callback_query(F.data == "update_location")
async def cb_update_location(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer("📍 Yangi lokatsiyangizni ulashing:", reply_markup=location_request_kb())


@router.callback_query(F.data.startswith("search_medicine:"))
async def cb_search_medicine(callback: CallbackQuery) -> None:
    """Alomat sahifasidan dori qidirish."""
    await callback.answer()
    medicine_name = callback.data.split(":", 1)[1]
    await callback.message.answer(f"🔍 {medicine_name.capitalize()} qidirilmoqda...")

    db_user = await queries.get_user(callback.from_user.id)
    if not db_user or not db_user.get("lat"):
        await callback.message.answer("📍 Avval lokatsiyangizni ulashing!")
        return

    result = await search_service.search_medicine(
        user_query=medicine_name,
        user_lat=db_user["lat"],
        user_lng=db_user["lng"],
        telegram_id=callback.from_user.id,
    )

    if result.get("image_url"):
        try:
            from aiogram.types import URLInputFile
            await callback.message.answer_photo(
                photo=URLInputFile(result["image_url"]),
                caption=f"💊 <b>{result['display_name']}</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass

    alt_text = format_generic_alternatives(result.get("generic_alternatives", []), result["display_name"])
    full_text = result["text"] + alt_text if alt_text else result["text"]
    mid = result.get("medicine_id")
    kb = search_with_watch_kb(mid) if mid else search_again_kb()
    await callback.message.answer(full_text, parse_mode="HTML", reply_markup=kb)
