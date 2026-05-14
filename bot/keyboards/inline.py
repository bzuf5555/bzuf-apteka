from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def pharmacy_detail_kb(pharmacy_id: int, lat: float, lng: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🗺️ Xaritada ko'rish",
                url=f"https://www.google.com/maps?q={lat},{lng}",
            )],
        ]
    )


def search_again_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Yana qidirish", callback_data="search_again")],
            [InlineKeyboardButton(text="📍 Lokatsiyani yangilash", callback_data="update_location")],
        ]
    )


def search_with_watch_kb(medicine_id: str, is_watching: bool = False) -> InlineKeyboardMarkup:
    """Qidiruv natijalari + narq kuzatuvi tugmasi."""
    watch_text = "🔕 Kuzatuvdan chiqish" if is_watching else "🔔 Narq tushsa xabar ber"
    watch_data = f"unwatch:{medicine_id}" if is_watching else f"watch:{medicine_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=watch_text, callback_data=watch_data)],
            [InlineKeyboardButton(text="🔍 Yana qidirish", callback_data="search_again")],
            [InlineKeyboardButton(text="📍 Lokatsiyani yangilash", callback_data="update_location")],
        ]
    )
