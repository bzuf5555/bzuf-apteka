import asyncio
from loguru import logger
from aiogram import Bot
from bot.database import queries

THRESHOLD      = 0.15
CHECK_INTERVAL = 6 * 3600


async def check_all_watches(bot: Bot) -> None:
    watches = await queries.get_active_watches()
    if not watches:
        return

    logger.info(f"Narq tekshiruvi: {len(watches)} ta obuna")
    notified = 0

    for watch in watches:
        try:
            current_min = await queries.get_current_min_price(
                medicine_id=watch["medicine_id"],
                user_lat   =watch["user_lat"],
                user_lng   =watch["user_lng"],
            )
            if current_min is None:
                continue

            old_price  = watch.get("min_price", 0)
            if old_price <= 0:
                await queries.update_watch_price(watch["_id"], current_min)
                continue

            drop = (old_price - current_min) / old_price
            if drop >= THRESHOLD:
                drop_pct = int(drop * 100)
                name     = watch.get("medicine_name", "Dori")

                await bot.send_message(
                    chat_id   = watch["telegram_id"],
                    text      = (
                        f"💰 <b>Narq tushdi!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"💊 <b>{name}</b>\n"
                        f"📉 Ilgari:  <s>{int(old_price):,} so'm</s>\n"
                        f"✅ Hozir:   <b>{int(current_min):,} so'm</b>  (−{drop_pct}%)\n\n"
                        f"Qidirish uchun dori nomini yuboring 👇"
                    ),
                    parse_mode="HTML",
                )
                notified += 1
                await queries.update_watch_price(watch["_id"], current_min)

            elif current_min < old_price:
                await queries.update_watch_price(watch["_id"], current_min)

        except Exception as e:
            logger.error(f"Watch xatosi {watch.get('_id')}: {e}")
        finally:
            await asyncio.sleep(0.1)

    if notified:
        logger.success(f"Narq xabarlari: {notified} ta yuborildi")


async def price_watch_loop(bot: Bot) -> None:
    logger.info("Narq kuzatuvi ishga tushdi")
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            await check_all_watches(bot)
        except Exception as e:
            logger.error(f"Narq kuzatuvi xatosi: {e}")
