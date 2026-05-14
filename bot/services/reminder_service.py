"""
Dori eslatma xizmati.
Har daqiqada faol eslatmalarni tekshiradi va mos vaqtda xabar yuboradi.
"""
import asyncio
import datetime
from loguru import logger
from aiogram import Bot
from bot.database import queries

TZ = datetime.timezone(datetime.timedelta(hours=5))


async def reminder_loop(bot: Bot) -> None:
    logger.info("Dori eslatma xizmati ishga tushdi")
    while True:
        await asyncio.sleep(60)  # har daqiqada
        try:
            await _check_reminders(bot)
        except Exception as e:
            logger.error(f"Eslatma xatosi: {e}")


async def _check_reminders(bot: Bot) -> None:
    now = datetime.datetime.now(TZ)
    current_time = now.strftime("%H:%M")

    reminders = await queries.get_active_reminders()
    for r in reminders:
        if current_time in r.get("times", []):
            try:
                await bot.send_message(
                    chat_id=r["telegram_id"],
                    text=(
                        f"⏰ <b>Dori vaqti!</b>\n\n"
                        f"💊 <b>{r['medicine_name']}</b> ichish vaqti keldi.\n\n"
                        f"<i>Eslatmani bekor qilish: /remind</i>"
                    ),
                    parse_mode="HTML",
                )
                logger.info(f"Eslatma yuborildi: {r['telegram_id']} → {r['medicine_name']}")
            except Exception as e:
                logger.warning(f"Eslatma yuborib bo'lmadi {r['telegram_id']}: {e}")
