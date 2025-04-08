from aiogram import Router, F
from aiogram.types import Message
from services.payment_service import log_pending_payment
from services.yookassa_service import create_yookassa_payment
from keyboards.shop import (
    get_question_packages_keyboard,
    get_subscription_packages_keyboard
)
from aiogram.fsm.context import FSMContext
from utils.context_stack import push_step

router = Router()

# Универсальная функция отправки ссылки на оплату
async def send_payment_link(message: Message, amount: int, description: str, payment_type: str, quantity: int):
    user_id = message.from_user.id

    try:
        payment_link, internal_id = await create_yookassa_payment(
            user_id=user_id,
            amount=amount,
            description=description,
            payment_type=payment_type,
            quantity=quantity
        )

        await log_pending_payment(user_id, internal_id, quantity, payment_type)

        await message.answer(
            f"🧾 <b>Оплата</b>\n\n"
            f"{description} за {amount}₽.\n"
            f"Перейди по ссылке, чтобы оплатить:\n\n"
            f"<a href='{payment_link}'>💳 Оплатить через YooKassa</a>",
            disable_web_page_preview=True
        )
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки:\n<code>{str(e)}</code>")


# Обработка кнопки "🧾 Купить вопросы"
@router.message(F.text == "🧾 Купить вопросы")
async def show_question_packages(message: Message, state: FSMContext):
    await push_step(state, "shop")
    await message.answer(
        "📦 <b>Выберите пакет вопросов:</b>",
        reply_markup=get_question_packages_keyboard()
    )

# Обработка кнопки "🔓 Купить подписку"
@router.message(F.text == "🔓 Купить подписку")
async def show_subscription_packages(message: Message, state: FSMContext):
    await push_step(state, "shop")
    await message.answer(
        "🔓 <b>Лайт — 149₽</b>\n"
        "• Безлимит на 7 дней\n"
        "• XP не начисляется\n"
        "• Участие в челленджах\n"
        "• Приоритет в ответах\n\n"
        "🔐 <b>Про — 499₽</b>\n"
        "• Всё из Лайт\n"
        "• +100 вопросов\n"
        "• До 3 видео по теме\n"
        "• Генерация изображений\n"
        "• Максимальный приоритет\n\n"
        "💼 <b>Выберите подписку:</b>",
        reply_markup=get_subscription_packages_keyboard()
    )

# Обработчики кнопок в магазине

@router.message(F.text == "🔓 Лайт / 7 дней")
async def buy_light_subscription(message: Message):
    await send_payment_link(
        message,
        amount=149,
        description="Подписка Лайт на 7 дней",
        payment_type="subscription",
        quantity=7
    )

@router.message(F.text == "🔓 Про / 30 дней")
async def buy_pro_subscription(message: Message):
    await send_payment_link(
        message,
        amount=299,
        description="Подписка Про на 30 дней",
        payment_type="subscription",
        quantity=30
    )

@router.message(F.text == "🧾 1 вопрос — 10₽")
async def buy_1_question(message: Message):
    await send_payment_link(
        message,
        amount=10,
        description="Покупка 1 вопроса",
        payment_type="questions",
        quantity=1
    )

@router.message(F.text == "🧾 10 вопросов — 90₽")
async def buy_10_questions(message: Message):
    await send_payment_link(
        message,
        amount=90,
        description="Покупка 10 вопросов",
        payment_type="questions",
        quantity=10
    )

@router.message(F.text == "🧾 50 вопросов — 450₽")
async def buy_50_questions(message: Message):
    await send_payment_link(
        message,
        amount=450,
        description="Покупка 50 вопросов",
        payment_type="questions",
        quantity=50
    )

@router.message(F.text == "🧾 100 вопросов — 900₽")
async def buy_100_questions(message: Message):
    await send_payment_link(
        message,
        amount=900,
        description="Покупка 100 вопросов",
        payment_type="questions",
        quantity=100
    )

