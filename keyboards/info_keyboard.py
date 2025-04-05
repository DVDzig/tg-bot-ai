from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_info_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎖️ Статусы", callback_data="info_statuses")],
        [InlineKeyboardButton(text="💳 Подписки", callback_data="info_subscriptions")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="info_help")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back:main")]
    ])
