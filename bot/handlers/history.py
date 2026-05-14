from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import queries

router = Router()


@router.message(Command("history"))
@router.message(F.text == "🕐 Tarix")
async def cmd_history(message: Message) -> None:
    history = await queries.get_search_history(message.from_user.id)
    if not history:
        await message.answer(
            "🕐 <b>Qidiruv tarixi</b>\n\nHali hech narsa qidirmadingiz.",
            parse_mode="HTML",
        )
        return

    lines = ["🕐 <b>So'nggi qidiruvlar:</b>\n"]
    for i, h in enumerate(history, 1):
        searched_at = h.get("searched_at")
        time_str = searched_at.strftime("%d.%m %H:%M") if searched_at else ""
        count = h.get("results_count", 0)
        lines.append(f"{i}. <b>{h['query']}</b> — {count} ta dorixona  <i>{time_str}</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")
