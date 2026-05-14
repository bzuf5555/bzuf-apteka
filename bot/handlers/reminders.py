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
    waiting_times = State()


@router.message(Command("remind"))
async def cmd_remind(message: Message, state: FSMContext) -> None:
    reminders = await queries.get_user_reminders(message.from_user.id)
    if reminders:
        await message.answer(
            f"⏰ <b>Sizning eslatmalaringiz</b> ({len(reminders)} ta):\n"
            "O'chirish uchun 🗑 tugmasini bosing 👇",
            reply_markup=reminder_list_kb(reminders),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "⏰ <b>Dori eslatma</b>\n\n"
            "Qaysi dori uchun eslatma qo'yishni xohlaysiz?\n"
            "<i>Masalan: Metformin</i>",
            parse_mode="HTML",
        )
        await state.set_state(ReminderForm.waiting_medicine)


@router.callback_query(F.data == "new_reminder")
async def cb_new_reminder(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.answer(
        "⏰ Qaysi dori uchun eslatma qo'yamiz?\n<i>Masalan: Metformin</i>",
        parse_mode="HTML",
    )
    await state.set_state(ReminderForm.waiting_medicine)


@router.message(ReminderForm.waiting_medicine)
async def got_medicine_name(message: Message, state: FSMContext) -> None:
    await state.update_data(medicine_name=message.text.strip())
    await message.answer(
        f"✅ <b>{message.text.strip()}</b>\n\n"
        "⏰ Qachon eslatay? Vaqtni yozing:\n"
        "<i>Masalan: 08:00 yoki 08:00, 20:00</i>",
        parse_mode="HTML",
    )
    await state.set_state(ReminderForm.waiting_times)


@router.message(ReminderForm.waiting_times)
async def got_times(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    # Parse vaqtlar: "08:00, 20:00" yoki "08:00 va 20:00"
    times = re.findall(r"\b(\d{1,2}:\d{2})\b", text)
    if not times:
        await message.answer("❌ Vaqtni to'g'ri yozing: masalan <b>08:00</b> yoki <b>08:00, 20:00</b>", parse_mode="HTML")
        return

    data = await state.get_data()
    medicine_name = data.get("medicine_name", "Dori")
    await queries.create_reminder(message.from_user.id, medicine_name, times)
    await state.clear()

    times_str = " va ".join(times)
    await message.answer(
        f"✅ <b>Eslatma qo'yildi!</b>\n\n"
        f"💊 Dori: <b>{medicine_name}</b>\n"
        f"⏰ Vaqt: <b>{times_str}</b>\n\n"
        f"Har kuni shu vaqtlarda eslataman!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
    logger.info(f"Eslatma: {message.from_user.id} → {medicine_name} @ {times}")


@router.callback_query(F.data.startswith("del_reminder:"))
async def cb_del_reminder(callback: CallbackQuery) -> None:
    await callback.answer()
    rid_str = callback.data.split(":", 1)[1]
    try:
        rid = ObjectId(rid_str)
    except Exception:
        return
    await queries.delete_reminder(rid)
    await callback.answer("🗑 Eslatma o'chirildi", show_alert=False)

    reminders = await queries.get_user_reminders(callback.from_user.id)
    if reminders:
        await callback.message.edit_reply_markup(reply_markup=reminder_list_kb(reminders))
    else:
        await callback.message.edit_text("⏰ Eslatmalar yo'q.", reply_markup=None)
