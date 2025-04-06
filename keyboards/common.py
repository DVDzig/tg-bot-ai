from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_back_keyboard(placeholder: str = "Выберите действие ⤵️") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )
