from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_rating_keyboard() -> InlineKeyboardMarkup:
    emojis = ["🤩", "😊", "😐", "🙁", "😡"]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=emoji, callback_data=f"rating:{emoji}") for emoji in emojis]
        ]
    )
