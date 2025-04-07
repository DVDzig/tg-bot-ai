from aiogram.types import ReplyKeyboardMarkup, KeyboardButton



def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="🏆 Топ-10")],
        [KeyboardButton(text="🔓 Выдать Лайт")],
        [KeyboardButton(text="🔐 Выдать Про")],
        [KeyboardButton(text="♻️ Сброс лимитов")],
        [KeyboardButton(text="📣 Рассылка")],
        [KeyboardButton(text="🔁 Обновить ключевые слова")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ⤵️"
    )
