from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

REMOVE = ReplyKeyboardRemove()


def contact_request_kb() -> ReplyKeyboardMarkup:
    """Telefon raqamini so'rash (1-qadam)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktimni ulashish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Telefon raqamingizni ulashing...",
    )


def location_request_kb() -> ReplyKeyboardMarkup:
    """Lokatsiya so'rash (2-qadam)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Lokatsiyamni ulashish", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Joylashuvingizni ulashing...",
    )


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Asosiy menyu — faqat to'liq ro'yxatdan o'tgan foydalanuvchilar uchun."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Dori qidirish")],
            [
                KeyboardButton(text="📍 Lokatsiyani yangilash", request_location=True),
                KeyboardButton(text="ℹ️ Yordam"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Dori nomini kiriting...",
    )
