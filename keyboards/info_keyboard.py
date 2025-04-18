from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_info_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎖️ Статусы"), KeyboardButton(text="💳 Подписки")],
        [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="✉️ Обратная связь")],
        [KeyboardButton(text="⬅️ Назад в главное меню")]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел ⤵️"
    )
