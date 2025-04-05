from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_question_packages_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 1 вопрос — 10₽", callback_data="buy_questions_1")
    builder.button(text="🧾 10 вопросов — 90₽", callback_data="buy_questions_10")
    builder.button(text="🧾 50 вопросов — 450₽", callback_data="buy_questions_50")
    builder.button(text="🧾 100 вопросов — 900₽", callback_data="buy_questions_100")
    builder.button(text="⬅️ Назад", callback_data="shop_back")
    builder.adjust(1)
    return builder.as_markup()

def get_subscription_packages_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔓 Лайт — 149₽ / 7 дней", callback_data="buy_sub_lite")
    builder.button(text="🔓 Про — 499₽ / 30 дней", callback_data="buy_sub_pro")
    builder.button(text="⬅️ Назад", callback_data="shop_back")
    builder.adjust(1)
    return builder.as_markup()
