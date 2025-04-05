from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_back_keyboard(target: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back:{target}")]
        ]
    )
