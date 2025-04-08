from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_shop_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧾 Купить вопросы")],
            [KeyboardButton(text="🔓 Купить подписку")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел ⤵️"
    )

def get_question_packages_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧾 1 вопрос — 10₽")],
            [KeyboardButton(text="🧾 10 вопросов — 90₽")],
            [KeyboardButton(text="🧾 50 вопросов — 450₽")],
            [KeyboardButton(text="🧾 100 вопросов — 900₽")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите пакет ⤵️"
    )

def get_subscription_packages_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔓 Лайт — 149₽ / 7 дней")],
            [KeyboardButton(text="🔓 Про — 499₽ / 30 дней")],
            [KeyboardButton(text="⬅️ Назад")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите подписку ⤵️"
    )
