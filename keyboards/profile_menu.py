from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_profile_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="👥 Рефералы"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📄 Мои вопросы")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Раздел «Профиль»"
    )

