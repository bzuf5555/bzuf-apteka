"""MongoDB indexlarini yaratadi. Xavfsiz qayta chaqirish mumkin."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.database.connection import get_db, close_db
from bot.database.models import create_indexes
from loguru import logger


async def migrate() -> None:
    db = await get_db()
    await create_indexes(db)
    logger.success("Barcha indexlar yaratildi!")
    await close_db()


if __name__ == "__main__":
    asyncio.run(migrate())
