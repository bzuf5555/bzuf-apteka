from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.keyboards.reply import contact_request_kb, main_menu_kb

router = Router()

_NO_CONTACT_FIRST = """⚠️ Avval telefon raqamingizni ulashing.

Quyidagi tugmani bosing 👇"""

_LOCATION_SAVED = """✅ <b>Joylashuvingiz saqlandi!</b>

Endi botdan to'liq foydalanishingiz mumkin.
Dori nomini yozing yoki menyu tugmasini bosing 👇"""

_LOCATION_UPDATED = """✅ <b>Joylashuv yangilandi!</b>

Yangi manzil asosida qidirish mumkin."""


@router.message(F.location)
async def handle_location(message: Message) -> None:
    user = message.from_user
    loc = message.location

    if not await queries.user_has_contact(user.id):
        await message.answer(_NO_CONTACT_FIRST, reply_markup=contact_request_kb(), parse_mode="HTML")
        return

    was_first_time = not await queries.user_has_location(user.id)

    await queries.update_user_location(
        telegram_id=user.id,
        lat=loc.latitude,
        lng=loc.longitude,
    )

    text = _LOCATION_SAVED if was_first_time else _LOCATION_UPDATED
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
    logger.info(f"Lokatsiya: {user.id} → ({loc.latitude:.4f}, {loc.longitude:.4f})")
