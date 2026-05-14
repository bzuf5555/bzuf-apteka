from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from bson import ObjectId
from loguru import logger

from bot.database import queries
from bot.keyboards.inline import saved_medicines_kb

router = Router()


@router.message(Command("my_medicines"))
@router.message(F.text == "⭐ Mening dorilarim")
async def cmd_my_medicines(message: Message) -> None:
    saved = await queries.get_saved_medicines(message.from_user.id)
    if not saved:
        await message.answer(
            "⭐ <b>Mening dorilarim</b>\n\nHali hech narsa saqlanmagan.\n"
            "Dori qidirganingizda <b>⭐ Saqlash</b> tugmasini bosing.",
            parse_mode="HTML",
        )
        return
    await message.answer(
        f"⭐ <b>Mening dorilarim</b> ({len(saved)} ta):\n"
        "Qidirish uchun nomini bosing 👇",
        reply_markup=saved_medicines_kb(saved),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("save:"))
async def cb_save(callback: CallbackQuery) -> None:
    await callback.answer()
    med_id_str = callback.data.split(":", 1)[1]
    try:
        med_id = ObjectId(med_id_str)
    except Exception:
        return

    med = await queries.get_medicine_by_id(med_id)
    name = med.get("name_uz", "Dori") if med else "Dori"
    await queries.save_medicine(callback.from_user.id, med_id, name)
    await callback.answer(f"⭐ {name} saqlandi!", show_alert=False)
    logger.info(f"Saqlandi: {callback.from_user.id} → {name}")


@router.callback_query(F.data.startswith("unsave:"))
async def cb_unsave(callback: CallbackQuery) -> None:
    await callback.answer()
    med_id_str = callback.data.split(":", 1)[1]
    try:
        med_id = ObjectId(med_id_str)
    except Exception:
        return
    await queries.remove_saved_medicine(callback.from_user.id, med_id)
    await callback.answer("🗑 O'chirildi", show_alert=False)

    # Ro'yxatni yangilash
    saved = await queries.get_saved_medicines(callback.from_user.id)
    if saved:
        await callback.message.edit_reply_markup(reply_markup=saved_medicines_kb(saved))
    else:
        await callback.message.edit_text("⭐ Saqlangan dorilar ro'yxati bo'sh.", reply_markup=None)


@router.callback_query(F.data.startswith("search_saved:"))
async def cb_search_saved(callback: CallbackQuery) -> None:
    """Saqlangan dorini qidirish."""
    await callback.answer()
    med_id_str = callback.data.split(":", 1)[1]
    try:
        med_id = ObjectId(med_id_str)
    except Exception:
        return

    med = await queries.get_medicine_by_id(med_id)
    if not med:
        await callback.answer("Dori topilmadi", show_alert=True)
        return

    # search handler ga yo'naltirish
    await callback.message.answer(
        f"🔍 <b>{med['name_uz']}</b> qidirilmoqda...",
        parse_mode="HTML",
    )
    # Fake message trigger — search handler chaqiramiz
    from bot.services import search_service
    from bot.keyboards.inline import search_with_watch_kb, search_again_kb
    from bot.agents.search_agent import format_generic_alternatives

    user = callback.from_user
    db_user = await queries.get_user(user.id)
    if not db_user or not db_user.get("lat"):
        await callback.message.answer("📍 Avval lokatsiyangizni ulashing!")
        return

    result = await search_service.search_medicine(
        user_query=med["name_uz"],
        user_lat=db_user["lat"],
        user_lng=db_user["lng"],
        telegram_id=user.id,
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
