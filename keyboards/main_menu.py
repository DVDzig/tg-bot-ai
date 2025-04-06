from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID


def get_main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    print(f"🧪 get_main_menu_keyboard → user_id={user_id}, ADMIN_ID={ADMIN_ID}")
    buttons = [
        [KeyboardButton(text="💬 Выбор программы")],
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="📊 ТОП-10")],
        [KeyboardButton(text="🎯 Миссии"), KeyboardButton(text="🛒 Магазин")],
        [KeyboardButton(text="ℹ️ Info")]
    ]

    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="🛠 Админ")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ⤵️"
    )
