import re
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from bson import ObjectId
from loguru import logger

from bot.database import queries
from bot.keyboards.inline import reminder_list_kb
from bot.keyboards.reply import main_menu_kb

router = Router()


class ReminderForm(StatesGroup):
    waiting_medicine = State()
    waiting_times    = State()


@router.message(Command("remind"))
async def cmd_remind(message: Message, state: FSMContext) -> None:
    reminders = await queries.get_user_reminders(message.from_user.id)
    if reminders:
        lines = ["⏰ <b>Faol eslatmalar:</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
        for r in reminders:
            times_s = "  ".join(r.get("times", []))
            lines.append(f"💊 <b>{r['medicine_name']}</b>  🕐 {times_s}")
        lines.append("\n━━━━━━━━━━━━━━━━━━━━\nO'chirish uchun tugmani bosing 👇")
        await message.answer(
            "\n".join(lines),
            reply_markup=reminder_list_kb(reminders),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "⏰ <b>Dori eslatma</b>\n\n"
            "Qaysi dori uchun eslatma qo'yamiz?\n"
            "<i>Masalan: Metformin</i>",
            parse_mode="HTML",
        )
        await state.set_state(ReminderForm.waiting_medicine)


@router.callback_query(F.data == "new_reminder")
async def cb_new_reminder(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        "⏰ <b>Yangi eslatma</b>\n\n"
        "Qaysi dori uchun eslatma qo'yamiz?\n"
        "<i>Masalan: Metformin, Bisoprolol</i>",
        parse_mode="HTML",
    )
    await state.set_state(ReminderForm.waiting_medicine)


@router.message(ReminderForm.waiting_medicine)
async def got_medicine_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    await state.update_data(medicine_name=name)
    await message.answer(
        f"💊 <b>{name}</b>\n\n"
        f"⏰ Soatni yozing:\n"
        f"<i>Masalan: 08:00   yoki   08:00, 20:00</i>",
        parse_mode="HTML",
    )
    await state.set_state(ReminderForm.waiting_times)


@router.message(ReminderForm.waiting_times)
async def got_times(message: Message, state: FSMContext) -> None:
    times = re.findall(r"\b(\d{1,2}:\d{2})\b", message.text)
    if not times:
        await message.answer(
            "❌ Vaqtni to'g'ri yozing:\n<b>08:00</b>  yoki  <b>08:00, 20:00</b>",
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    name = data.get("medicine_name", "Dori")
    await queries.create_reminder(message.from_user.id, name, times)
    await state.clear()

    times_s = "  ·  ".join(times)
    await message.answer(
        f"✅ <b>Eslatma qo'yildi!</b>\n\n"
        f"💊 {name}\n"
        f"🕐 Har kuni:  <b>{times_s}</b>\n\n"
        f"<i>Bekor qilish: /remind</i>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
    logger.info(f"Eslatma: {message.from_user.id} → {name} @ {times}")


@router.callback_query(F.data.startswith("del_reminder:"))
async def cb_del_reminder(callback: CallbackQuery) -> None:
    await callback.answer()
    rid_s = callback.data.split(":", 1)[1]
    try:
        await queries.delete_reminder(ObjectId(rid_s))
    except Exception:
        pass
    await callback.answer("🗑 O'chirildi", show_alert=False)

    reminders = await queries.get_user_reminders(callback.from_user.id)
    if reminders:
        await callback.message.edit_reply_markup(reply_markup=reminder_list_kb(reminders))
    else:
        await callback.message.edit_text(
            "⏰ Barcha eslatmalar o'chirildi.\n"
            "Yangi eslatma qo'shish uchun /remind yuboring.",
            reply_markup=None,
        )
