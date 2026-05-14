from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from bot.database import queries

router = Router()


@router.message(Command("history"))
@router.message(F.text == "🕐 Tarix")
async def cmd_history(message: Message) -> None:
    history = await queries.get_search_history(message.from_user.id, limit=10)
    if not history:
        await message.answer(
            "🕐 <b>Qidiruv tarixi</b>\n\n"
            "Hali hech narsa qidirmadingiz.\n"
            "Dori nomini yozing — tarix shu yerda ko'rinadi.",
            parse_mode="HTML",
        )
        return

    lines = ["🕐 <b>So'nggi qidiruvlar:</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
    for i, h in enumerate(history, 1):
        t       = h.get("searched_at")
        time_s  = t.strftime("%d.%m  %H:%M") if t else ""
        count   = h.get("results_count", 0)
        found   = f"✅ {count} ta" if count else "❌ topilmadi"
        lines.append(f"{i}. <b>{h['query']}</b>\n   {found}  •  <i>{time_s}</i>\n")

    await message.answer("\n".join(lines), parse_mode="HTML")
