from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.keyboards.reply import contact_request_kb, location_request_kb, main_menu_kb

router = Router()

_STEP1_CONTACT = """👋 Salom, <b>{name}</b>!

🏥 <b>Dorixona Qidiruv</b> botiga xush kelibsiz!

Bu bot orqali:
• Yaqin atrofdagi dorixonalarda dori bor-yo'qligini bilasiz
• Narxlarni solishtira olasiz
• Xaritada dorixona manzilini ko'rasiz

━━━━━━━━━━━━━━━━━━━━━
<b>1-qadam:</b> Telefon raqamingizni ulashing 👇

<i>Bu faqat xavfsizlik maqsadida — boshqa maqsadda ishlatilmaydi.</i>"""

_STEP2_LOCATION = """✅ <b>Telefon raqamingiz saqlandi!</b>

━━━━━━━━━━━━━━━━━━━━━
<b>2-qadam:</b> Joylashuvingizni ulashing 👇

<i>Bot sizga yaqin dorixonalarni topadi.</i>"""

_WELCOME_BACK = """👋 Xush kelibsiz, <b>{name}</b>!

🔍 Qaysi dorini qidiryapsiz?
Dori nomini yozing yoki menyu tugmasini bosing."""

_HELP_TEXT = """ℹ️ <b>Yordam</b>

<b>Qanday foydalanish:</b>
1️⃣ Telefon raqamingizni ulashing
2️⃣ Joylashuvingizni ulashing
3️⃣ Dori nomini yozing

<b>Misol so'rovlar:</b>
• <i>Paracetamol</i>
• <i>Ibuprofen 400mg</i>
• <i>Amoxicillin</i>
• <i>Парацетамол</i>
• <i>No-shpa</i>

Bot {radius} km doiradagi dorixonalarni ko'rsatadi.

<b>Muammo?</b> @admin ga yozing"""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await queries.upsert_user(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name or user.first_name,
    )

    has_contact = await queries.user_has_contact(user.id)
    has_location = await queries.user_has_location(user.id)

    if has_contact and has_location:
        await message.answer(
            _WELCOME_BACK.format(name=user.first_name),
            reply_markup=main_menu_kb(),
            parse_mode="HTML",
        )
    elif has_contact:
        await message.answer(_STEP2_LOCATION, reply_markup=location_request_kb(), parse_mode="HTML")
    else:
        await message.answer(
            _STEP1_CONTACT.format(name=user.first_name),
            reply_markup=contact_request_kb(),
            parse_mode="HTML",
        )

    logger.info(f"/start: {user.id} contact={has_contact} location={has_location}")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: Message) -> None:
    from bot.config import settings
    await message.answer(
        _HELP_TEXT.format(radius=int(settings.SEARCH_RADIUS_KM)),
        parse_mode="HTML",
    )
