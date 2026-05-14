from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.keyboards.reply import contact_request_kb, location_request_kb, main_menu_kb

router = Router()

_STEP1 = """🏥 <b>Dorixona Qidiruv</b>

Assalomu alaykum, <b>{name}</b>!

Bu bot orqali siz:
💊 Yaqin dorixonalarda dori topasiz
💰 Narxlarni solishtirasiz
📍 Dorixona lokatsiyasini olasiz

━━━━━━━━━━━━━━━━━━━━
<b>1-qadam</b> — Telefon raqamingizni ulashing 👇
<i>Faqat xavfsizlik uchun, boshqa maqsadda ishlatilmaydi.</i>"""

_STEP2 = """✅ <b>Telefon raqam saqlandi!</b>

━━━━━━━━━━━━━━━━━━━━
<b>2-qadam</b> — Joylashuvingizni ulashing 👇
<i>Bot sizga yaqin dorixonalarni topadi.</i>"""

_WELCOME_BACK = """👋 Xush kelibsiz, <b>{name}</b>!

Qaysi dorini qidirasiz?
Dori nomini yozing yoki pastdagi menyudan foydalaning 👇"""

_HELP = """ℹ️ <b>Yordam</b>
━━━━━━━━━━━━━━━━━━━━

<b>Qanday foydalanish:</b>
1️⃣ Kontaktingizni ulashing
2️⃣ Lokatsiyangizni ulashing
3️⃣ Dori nomini yozing

<b>Qidiruv misollari:</b>
• <code>Paracetamol</code>
• <code>No-shpa</code>
• <code>Mexidol</code>
• <code>Boshim og'riyapti</code> ← alomat ham ishlaydi!

<b>Buyruqlar:</b>
/remind — dori eslatma qo'yish
/history — qidiruv tarixi
/my_medicines — saqlangan dorilar

━━━━━━━━━━━━━━━━━━━━
📏 Qidiruv doirasi: <b>{radius} km</b>"""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await queries.upsert_user(
        telegram_id=user.id,
        username=user.username,
        full_name=user.full_name or user.first_name,
    )
    has_contact  = await queries.user_has_contact(user.id)
    has_location = await queries.user_has_location(user.id)

    if has_contact and has_location:
        await message.answer(
            _WELCOME_BACK.format(name=user.first_name),
            reply_markup=main_menu_kb(), parse_mode="HTML",
        )
    elif has_contact:
        await message.answer(_STEP2, reply_markup=location_request_kb(), parse_mode="HTML")
    else:
        await message.answer(
            _STEP1.format(name=user.first_name),
            reply_markup=contact_request_kb(), parse_mode="HTML",
        )
    logger.info(f"/start: {user.id} contact={has_contact} location={has_location}")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: Message) -> None:
    from bot.config import settings
    await message.answer(
        _HELP.format(radius=int(settings.SEARCH_RADIUS_KM)),
        parse_mode="HTML",
    )
