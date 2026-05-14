"""
Narq kuzatuvi xizmati.
Har 6 soatda barcha obunalarni tekshiradi.
Narq ≥15% tushsa → foydalanuvchiga Telegram xabari yuboriladi.
"""
import asyncio
from loguru import logger
from aiogram import Bot

from bot.database import queries

THRESHOLD = 0.15   # 15% va undan ko'p tushsa xabar berish
CHECK_INTERVAL = 6 * 3600  # har 6 soatda


async def check_all_watches(bot: Bot) -> None:
    """Barcha faol kuzatuvlarni tekshiradi va kerak bo'lsa xabar yuboradi."""
    watches = await queries.get_active_watches()
    if not watches:
        return

    logger.info(f"Narq tekshiruvi: {len(watches)} ta obuna")
    notified = 0

    for watch in watches:
        try:
            current_min = await queries.get_current_min_price(
                medicine_id=watch["medicine_id"],
                user_lat=watch["user_lat"],
                user_lng=watch["user_lng"],
            )

            if current_min is None:
                continue

            old_price = watch.get("min_price", 0)
            if old_price <= 0:
                await queries.update_watch_price(watch["_id"], current_min)
                continue

            drop_ratio = (old_price - current_min) / old_price

            if drop_ratio >= THRESHOLD:
                drop_pct = int(drop_ratio * 100)
                medicine_name = watch.get("medicine_name", "Dori")

                text = (
                    f"💰 <b>Narq tushdi!</b>\n\n"
                    f"💊 <b>{medicine_name}</b>\n"
                    f"📉 Ilgari: <s>{int(old_price):,} so'm</s>\n"
                    f"✅ Hozir: <b>{int(current_min):,} so'm</b> "
                    f"(<b>−{drop_pct}%</b> arzonlashdi!)\n\n"
                    f"🔍 Botga borib dori qidiring!"
                )

                try:
                    await bot.send_message(
                        chat_id=watch["telegram_id"],
                        text=text,
                        parse_mode="HTML",
                    )
                    notified += 1
                    logger.info(
                        f"Xabar yuborildi: {watch['telegram_id']} "
                        f"→ {medicine_name} {old_price}→{current_min}"
                    )
                except Exception as send_err:
                    logger.warning(f"Xabar yuborib bo'lmadi {watch['telegram_id']}: {send_err}")

                await queries.update_watch_price(watch["_id"], current_min)

            elif current_min < old_price:
                await queries.update_watch_price(watch["_id"], current_min)

        except Exception as e:
            logger.error(f"Watch tekshiruv xatosi {watch.get('_id')}: {e}")
        finally:
            await asyncio.sleep(0.1)

    if notified:
        logger.success(f"Narq o'zgarishi: {notified} ta foydalanuvchiga xabar yuborildi")


async def price_watch_loop(bot: Bot) -> None:
    """Fon vazifasi — har 6 soatda narxlarni tekshiradi."""
    logger.info("Narq kuzatuvi fon vazifasi ishga tushdi")
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            await check_all_watches(bot)
        except Exception as e:
            logger.error(f"Narq kuzatuvi xatosi: {e}")
