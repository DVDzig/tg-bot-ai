from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_back_keyboard(context: str = "") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
