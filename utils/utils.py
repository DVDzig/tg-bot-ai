# utils.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_back_keyboard(context: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back:{context}")]]
    )
