from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.keyboards.reply import contact_request_kb, main_menu_kb

router = Router()


@router.message(F.location)
async def handle_location(message: Message) -> None:
    user = message.from_user
    loc  = message.location

    if not await queries.user_has_contact(user.id):
        await message.answer(
            "⚠️ Avval telefon raqamingizni ulashing.\n"
            "Quyidagi tugmani bosing 👇",
            reply_markup=contact_request_kb(),
            parse_mode="HTML",
        )
        return

    was_first = not await queries.user_has_location(user.id)
    await queries.update_user_location(user.id, loc.latitude, loc.longitude)

    if was_first:
        await message.answer(
            "✅ <b>Joylashuv saqlandi!</b>\n\n"
            "🎉 Botdan to'liq foydalanishingiz mumkin!\n"
            "Dori nomini yozing yoki menyudan tanlang 👇",
            reply_markup=main_menu_kb(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "📍 <b>Joylashuv yangilandi!</b>\n\n"
            "Yangi manzilingiz asosida qidirish mumkin.",
            reply_markup=main_menu_kb(),
            parse_mode="HTML",
        )
    logger.info(f"Lokatsiya: {user.id} → ({loc.latitude:.4f}, {loc.longitude:.4f})")
