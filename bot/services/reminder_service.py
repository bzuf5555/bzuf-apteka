import asyncio, datetime
from loguru import logger
from aiogram import Bot
from bot.database import queries

TZ = datetime.timezone(datetime.timedelta(hours=5))


async def reminder_loop(bot: Bot) -> None:
    logger.info("Dori eslatma xizmati ishga tushdi")
    while True:
        await asyncio.sleep(60)
        try:
            now          = datetime.datetime.now(TZ)
            current_time = now.strftime("%H:%M")
            reminders    = await queries.get_active_reminders()

            for r in reminders:
                if current_time in r.get("times", []):
                    try:
                        await bot.send_message(
                            chat_id   = r["telegram_id"],
                            text      = (
                                f"⏰ <b>Dori vaqti!</b>\n\n"
                                f"💊 <b>{r['medicine_name']}</b>\n"
                                f"Ichishni unutmang!\n\n"
                                f"<i>Bekor qilish: /remind</i>"
                            ),
                            parse_mode="HTML",
                        )
                        logger.info(f"Eslatma: {r['telegram_id']} → {r['medicine_name']}")
                    except Exception as e:
                        logger.warning(f"Eslatma yuborib bo'lmadi {r['telegram_id']}: {e}")
        except Exception as e:
            logger.error(f"Eslatma xizmati xatosi: {e}")
