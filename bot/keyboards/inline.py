from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def search_with_watch_kb(medicine_id: str, is_watching: bool = False, is_saved: bool = False) -> InlineKeyboardMarkup:
    watch_text = "🔕 Kuzatuvdan chiqish" if is_watching else "🔔 Narq tushsa xabar ber"
    watch_data = f"unwatch:{medicine_id}" if is_watching else f"watch:{medicine_id}"
    save_text = "✅ Saqlangan" if is_saved else "⭐ Saqlash"
    save_data = f"unsave:{medicine_id}" if is_saved else f"save:{medicine_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=watch_text, callback_data=watch_data),
         InlineKeyboardButton(text=save_text, callback_data=save_data)],
        [InlineKeyboardButton(text="🔍 Yana qidirish", callback_data="search_again")],
        [InlineKeyboardButton(text="📍 Lokatsiyani yangilash", callback_data="update_location")],
    ])


def search_again_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Yana qidirish", callback_data="search_again")],
        [InlineKeyboardButton(text="📍 Lokatsiyani yangilash", callback_data="update_location")],
    ])


def symptom_medicines_kb(medicine_names: list[str]) -> InlineKeyboardMarkup:
    """Alomat natijasi — har bir dori uchun qidiruv tugmasi."""
    buttons = [
        [InlineKeyboardButton(text=f"🔍 {name.capitalize()}", callback_data=f"search_medicine:{name}")]
        for name in medicine_names[:4]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def saved_medicines_kb(medicines: list[dict]) -> InlineKeyboardMarkup:
    """Saqlangan dorilar — har biri uchun qidiruv + o'chirish."""
    buttons = []
    for m in medicines[:8]:
        mid = str(m["medicine_id"])
        name = m["medicine_name"][:20]
        buttons.append([
            InlineKeyboardButton(text=f"🔍 {name}", callback_data=f"search_saved:{mid}"),
            InlineKeyboardButton(text="🗑", callback_data=f"unsave:{mid}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def reminder_list_kb(reminders: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for r in reminders:
        rid = str(r["_id"])
        times_str = ", ".join(r.get("times", []))
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {r['medicine_name'][:20]} ({times_str})",
                callback_data=f"del_reminder:{rid}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="➕ Yangi eslatma", callback_data="new_reminder")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rating_kb(pharmacy_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⭐", callback_data=f"rate:{pharmacy_id}:1"),
        InlineKeyboardButton(text="⭐⭐", callback_data=f"rate:{pharmacy_id}:2"),
        InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"rate:{pharmacy_id}:3"),
        InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"rate:{pharmacy_id}:4"),
        InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"rate:{pharmacy_id}:5"),
    ]])
