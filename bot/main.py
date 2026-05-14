"""
Entry point.
- Development: polling mode
- Production (Render): webhook mode (aiohttp server, PORT env var)
"""

import asyncio
import os
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.database.connection import get_db, close_db
from bot.database.models import create_indexes
from bot.handlers import start, contact, location, search, admin, price_watch
from bot.handlers import my_medicines, reminders, ratings, history, location_cb
from bot.services.price_watch_service import price_watch_loop
from bot.services.reminder_service import reminder_loop


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="DEBUG" if not settings.is_production else "INFO",
        colorize=True,
    )
    if not settings.is_production:
        os.makedirs("logs", exist_ok=True)
        logger.add("logs/bot.log", rotation="10 MB", retention="7 days", level="INFO", encoding="utf-8")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(price_watch.router)
    dp.include_router(my_medicines.router)
    dp.include_router(reminders.router)
    dp.include_router(ratings.router)
    dp.include_router(history.router)
    dp.include_router(location_cb.router)
    dp.include_router(contact.router)
    dp.include_router(location.router)
    dp.include_router(search.router)
    dp.include_router(admin.router)
    return dp


async def _init_db() -> None:
    db = await get_db()
    await create_indexes(db)
    logger.success("MongoDB indexes tayyor")


# ── Polling (development) ──────────────────────────────────────────────────

async def run_polling() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    async def on_startup(bot: Bot) -> None:
        await _init_db()
        asyncio.create_task(price_watch_loop(bot))
        asyncio.create_task(reminder_loop(bot))
        me = await bot.get_me()
        logger.success(f"Polling: @{me.username}")

    async def on_shutdown(bot: Bot) -> None:
        await close_db()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


# ── Webhook (production / Render) ──────────────────────────────────────────

async def run_webhook() -> None:
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    async def on_startup(bot: Bot) -> None:
        await _init_db()
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        asyncio.create_task(price_watch_loop(bot))
        asyncio.create_task(reminder_loop(bot))
        me = await bot.get_me()
        logger.success(f"Webhook: @{me.username} → {settings.webhook_url}")

    async def on_shutdown(bot: Bot) -> None:
        await bot.delete_webhook()
        await close_db()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET,
    )
    handler.register(app, path=settings.webhook_path)

    # Render health check uchun
    async def health(_req):
        return web.Response(text="OK")
    app.router.add_get("/health", health)

    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 8000))
    logger.info(f"Webhook server port {port} da ishga tushmoqda")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.success(f"Server {port} portda ishlamoqda")

    await asyncio.Event().wait()


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    setup_logging()
    if settings.is_production and settings.WEBHOOK_HOST:
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())
