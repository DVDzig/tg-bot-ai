from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID

ADMIN_ID = int(ADMIN_ID)

def get_main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="💬 Выбор программы")],
        [
            KeyboardButton(text="👤 Мой профиль"),
            KeyboardButton(text="📊 ТОП-10")
        ],
        [
            KeyboardButton(text="🎯 Миссии"),
            KeyboardButton(text="🛒 Магазин")
        ],
        [KeyboardButton(text="ℹ️ Info")]
    ]

    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="🔧 Админ")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие ⭵️"
    )
