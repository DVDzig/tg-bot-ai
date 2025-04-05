from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="🏆 Топ-10", callback_data="admin_top")],
        [InlineKeyboardButton(text="🔓 Выдать Лайт", callback_data="admin_grant_lite")],
        [InlineKeyboardButton(text="🔐 Выдать Про", callback_data="admin_grant_pro")],
        [InlineKeyboardButton(text="♻️ Сброс лимитов", callback_data="admin_reset")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔁 Обновить ключевые слова", callback_data="admin_update_keywords")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
