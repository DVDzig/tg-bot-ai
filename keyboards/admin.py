from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="👥 Статистика пользователей")],
        [
            KeyboardButton(text="🏆 Топ по XP"), 
            KeyboardButton(text="🎫 Выдать подписку")
        ],
        [KeyboardButton(text="🔁 Обновить ключевые слова")],
        [
            KeyboardButton(text="♻️ Сброс лимитов"), 
            KeyboardButton(text="📣 Рассылка")
        ],
        [KeyboardButton(text="⬅️ Назад в главное меню")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ⤵️"
    )

def get_subscription_choice_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔑 Лайт"), KeyboardButton(text="🔒 Про")],
            [KeyboardButton(text="🔙 Назад в админ-панель")]
        ],
        resize_keyboard=True
    )