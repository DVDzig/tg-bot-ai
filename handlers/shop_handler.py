from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from handlers.shop_subscription_handler import generate_payment_link

router = Router()

# Открытие магазина
@router.message(F.text == "🛒 Магазин")
async def open_shop(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🧾 Вопросы", callback_data="shop_questions")
    builder.button(text="💳 Подписка", callback_data="shop_subscription")
    builder.button(text="⬅️ Назад", callback_data="back:main")
    builder.adjust(1)

    await message.answer(
        "🛍 <b>Добро пожаловать в Магазин</b>\n\n"
        "Здесь ты можешь:\n"
        "• Купить дополнительные вопросы\n"
        "• Оформить подписку с бонусами и безлимитом\n\n"
        "Выбери, что хочешь приобрести 👇",
        reply_markup=builder.as_markup()
    )

# Обработчик кнопки "Вопросы"
@router.callback_query(F.data == "shop_questions")
async def handle_shop_questions(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Купить 1 вопрос - 10₽", callback_data="purchase_1_question")
    builder.button(text="💳 Купить 10 вопросов - 90₽", callback_data="purchase_10_questions")
    builder.button(text="💳 Купить 50 вопросов - 450₽", callback_data="purchase_50_questions")
    builder.button(text="💳 Купить 100 вопросов - 900₽", callback_data="purchase_100_questions")
    builder.button(text="⬅️ Назад", callback_data="back:shop")
    builder.adjust(1)

    await call.message.edit_text(
        "🧾 <b>Выбор пакета вопросов</b>\n\n"
        "Выбери нужное количество вопросов 👇",
        reply_markup=builder.as_markup()
    )

# Обработчик кнопки "Подписка"
@router.callback_query(F.data == "shop_subscription")
async def handle_shop_subscription(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Подписка Лайт (7 дней) - 149₽", callback_data="purchase_light_subscription")
    builder.button(text="💳 Подписка Про - 299₽", callback_data="purchase_pro_subscription")
    builder.button(text="⬅️ Назад", callback_data="back:shop")
    builder.adjust(1)

    await call.message.edit_text(
        "💳 <b>Выбор подписки</b>\n\n"
        "Выбери подписку, чтобы оформить:\n"
        "• Лайт на 7 дней\n"
        "• Про на неограниченный срок\n\n"
        "Выбери, что хочешь приобрести 👇",
        reply_markup=builder.as_markup()
    )

# Обработчики для покупки вопросов

@router.callback_query(F.data == "purchase_1_question")
async def handle_single_question_purchase(call: CallbackQuery):
    user_id = call.from_user.id
    amount = 10
    description = "Покупка 1 вопроса"
    
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await call.message.answer(f"Для оплаты 1 вопроса перейди по ссылке: {payment_link}")
    except Exception as e:
        await call.message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

@router.callback_query(F.data == "purchase_10_questions")
async def handle_ten_questions_purchase(call: CallbackQuery):
    user_id = call.from_user.id
    amount = 90
    description = "Покупка 10 вопросов"
    
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await call.message.answer(f"Для оплаты 10 вопросов перейди по ссылке: {payment_link}")
    except Exception as e:
        await call.message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

@router.callback_query(F.data == "purchase_50_questions")
async def handle_fifty_questions_purchase(call: CallbackQuery):
    user_id = call.from_user.id
    amount = 450
    description = "Покупка 50 вопросов"
    
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await call.message.answer(f"Для оплаты 50 вопросов перейди по ссылке: {payment_link}")
    except Exception as e:
        await call.message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

@router.callback_query(F.data == "purchase_100_questions")
async def handle_hundred_questions_purchase(call: CallbackQuery):
    user_id = call.from_user.id
    amount = 900
    description = "Покупка 100 вопросов"
    
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await call.message.answer(f"Для оплаты 100 вопросов перейди по ссылке: {payment_link}")
    except Exception as e:
        await call.message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчики для подписки

# Обработчик для подписки (Лайт) — теперь на 7 дней
@router.callback_query(F.data == "purchase_light_subscription")
async def handle_light_subscription_payment(call: CallbackQuery):
    user_id = call.from_user.id
    amount = 149  # Подписка Лайт на 7 дней
    description = "Подписка Лайт на 7 дней"
    
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await call.message.answer(f"Для оплаты подписки Лайт перейди по ссылке: {payment_link}")
    except Exception as e:
        await call.message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчик для подписки (Про) — теперь на 30 дней
@router.callback_query(F.data == "purchase_pro_subscription")
async def handle_pro_subscription_payment(call: CallbackQuery):
    user_id = call.from_user.id
    amount = 299  # Подписка Про на 30 дней
    description = "Подписка Про на 30 дней"  # Изменили описание
    
    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await call.message.answer(f"Для оплаты подписки Про (30 дней) перейди по ссылке: {payment_link}")
    except Exception as e:
        await call.message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")
