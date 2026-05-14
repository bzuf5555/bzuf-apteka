from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.config import settings

router = Router()


def is_admin(tid: int) -> bool:
    return tid in settings.admin_ids


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    s = await queries.get_stats()
    await message.answer(
        f"📊 <b>Statistika</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Foydalanuvchilar:  <b>{s['users']:,}</b>\n"
        f"🏥 Dorixonalar:       <b>{s['pharmacies']:,}</b>\n"
        f"💊 Dorilar:           <b>{s['medicines']:,}</b>\n"
        f"📦 Inventar:          <b>{s['inventory']:,}</b>\n"
        f"🔍 Jami qidiruvlar:   <b>{s['searches']:,}</b>",
        parse_mode="HTML",
    )
    logger.info(f"Admin stats: {message.from_user.id}")
