from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def pharmacy_detail_kb(pharmacy_id: int, lat: float, lng: float) -> InlineKeyboardMarkup:
    """Dorixona tafsilotlari tugmalari."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗺️ Xaritada ko'rish",
                    url=f"https://www.google.com/maps?q={lat},{lng}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📞 Qo'ng'iroq qilish",
                    callback_data=f"call:{pharmacy_id}",
                ),
            ],
        ]
    )


def search_again_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Yana qidirish", callback_data="search_again")],
            [InlineKeyboardButton(text="📍 Lokatsiyani yangilash", callback_data="update_location")],
        ]
    )
