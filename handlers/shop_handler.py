from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from services.yookassa_service import generate_payment_link

router = Router()

def get_shop_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧾 Вопросы"), KeyboardButton(text="💳 Подписка")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ⤵️"
    )

def get_questions_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Купить 1 вопрос - 10₽")],
            [KeyboardButton(text="💳 Купить 10 вопросов - 90₽")],
            [KeyboardButton(text="💳 Купить 50 вопросов - 450₽")],
            [KeyboardButton(text="💳 Купить 100 вопросов - 900₽")],
            [KeyboardButton(text="⬅️ Назад в магазин")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите пакет ⤵️"
    )

def get_subscription_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Подписка Лайт (7 дней) - 149₽")],
            [KeyboardButton(text="💳 Подписка Про - 299₽")],
            [KeyboardButton(text="⬅️ Назад в магазин")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите подписку ⤵️"
    )

@router.message(F.text == "🛒 Магазин")
async def open_shop(message: Message):
    await message.answer(
        "🛍 <b>Добро пожаловать в Магазин</b>\n\n"
        "Здесь ты можешь:\n"
        "• Купить дополнительные вопросы\n"
        "• Оформить подписку с бонусами и безлимитом\n\n"
        "Выбери, что хочешь приобрести 👇",
        reply_markup=get_shop_keyboard()
    )

# Раздел Вопросов
@router.message(F.text == "🧾 Вопросы")
async def show_questions(message: Message):
    await message.answer(
        "🧾 <b>Выбор пакета вопросов</b>\n\n"
        "Выбери нужное количество вопросов 👇",
        reply_markup=get_questions_keyboard()
    )

@router.message(F.text == "💳 Купить 1 вопрос - 10₽")
async def buy_1_question(message: Message):
    await send_payment_link(message, 10, "Покупка 1 вопроса")

@router.message(F.text == "💳 Купить 10 вопросов - 90₽")
async def buy_10_questions(message: Message):
    await send_payment_link(message, 90, "Покупка 10 вопросов")

@router.message(F.text == "💳 Купить 50 вопросов - 450₽")
async def buy_50_questions(message: Message):
    await send_payment_link(message, 450, "Покупка 50 вопросов")

@router.message(F.text == "💳 Купить 100 вопросов - 900₽")
async def buy_100_questions(message: Message):
    await send_payment_link(message, 900, "Покупка 100 вопросов")

# Раздел Подписок
@router.message(F.text == "💳 Подписка")
async def show_subscription_options(message: Message):
    await message.answer(
        "💳 <b>Выбор подписки</b>\n\n"
        "Выбери подписку, чтобы оформить:\n"
        "• Лайт на 7 дней\n"
        "• Про на неограниченный срок\n\n"
        "Выбери, что хочешь приобрести 👇",
        reply_markup=get_subscription_keyboard()
    )

@router.message(F.text == "💳 Подписка Лайт (7 дней) - 149₽")
async def buy_light_subscription(message: Message):
    await send_payment_link(message, 149, "Подписка Лайт на 7 дней")

@router.message(F.text == "💳 Подписка Про - 299₽")
async def buy_pro_subscription(message: Message):
    await send_payment_link(message, 299, "Подписка Про на 30 дней")

# Возврат назад
@router.message(F.text.in_(["⬅️ Назад в магазин", "⬅️ Назад"]))
async def back_to_shop(message: Message):
    await open_shop(message)

# Общая функция оплаты
async def send_payment_link(message: Message, amount: int, description: str):
    user_id = message.from_user.id
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"💳 Для оплаты перейди по ссылке:\n{payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки:\n{str(e)}")
