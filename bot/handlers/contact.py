from aiogram import Router, F
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.keyboards.reply import location_request_kb

router = Router()


@router.message(F.contact)
async def handle_contact(message: Message) -> None:
    user    = message.from_user
    contact = message.contact

    if contact.user_id != user.id:
        await message.answer(
            "⚠️ Iltimos, <b>o'zingizning</b> kontaktingizni ulashing.\n"
            "Tugmani bosib o'zingiznikini yuboring 👇",
            parse_mode="HTML",
        )
        return

    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    full_name = " ".join(filter(None, [contact.first_name, contact.last_name]))
    await queries.save_user_contact(
        telegram_id=user.id,
        phone=phone,
        full_name=full_name or user.full_name or user.first_name,
    )

    await message.answer(
        f"✅ <b>Telefon raqam saqlandi!</b>\n"
        f"📱 {phone}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>2-qadam</b> — Joylashuvingizni ulashing 👇\n"
        f"<i>Bot sizga eng yaqin dorixonalarni topadi.</i>",
        reply_markup=location_request_kb(),
        parse_mode="HTML",
    )
    logger.info(f"Kontakt: {user.id} → {phone}")
