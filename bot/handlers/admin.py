from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from bot.database import queries
from bot.config import settings

router = Router()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    stats = await queries.get_stats()
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👤 Foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"🏥 Dorixonalar: <b>{stats['pharmacies']}</b>\n"
        f"💊 Doriler: <b>{stats['medicines']}</b>\n"
        f"📦 Inventar yozuvlari: <b>{stats['inventory']}</b>\n"
        f"🔍 Jami qidiruvlar: <b>{stats['searches']}</b>"
    )
    await message.answer(text, parse_mode="HTML")
    logger.info(f"Admin stats: {message.from_user.id}")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer("Broadcast funksiyasi hozircha mavjud emas.")
