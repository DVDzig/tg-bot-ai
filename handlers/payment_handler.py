import uuid
import yookassa
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from services.yookassa_service import Payment, generate_payment_link

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from handlers.shop_subscription_handler import log_pending_payment
from keyboards.shop import get_question_packages_keyboard


router = Router()

# Назначаем секретный ключ YooKassa
yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY

@router.message(F.text == "💳 Подписка")
async def handle_subscription_payment(message: Message):
    user_id = message.from_user.id
    # Пример: цена подписки на 7 дней
    amount = 500  # Платёжная сумма
    description = "Подписка Лайт на 7 дней"
    
    try:
        payment_link = generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты подписки перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

@router.callback_query(F.data.startswith("buy_questions_"))
async def handle_buy_questions(call: CallbackQuery):
    await call.answer()

    quantity = int(call.data.split("_")[-1])
    prices = {
        1: 10,
        10: 90,
        50: 450,
        100: 900,
    }

    amount = prices.get(quantity)
    if not amount:
        await call.message.answer("Ошибка: неизвестный пакет.")
        return

    payment_id = str(uuid.uuid4())
    user_id = call.from_user.id

    # Логируем ожидаемый платёж
    await log_pending_payment(user_id, payment_id, quantity, "questions")

    # Создаём платёж
    payment = Payment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/TGTutorBot"  # заменить на нужное
        },
        "capture": True,
        "description": f"{quantity} вопросов для user_id {user_id}",
        "metadata": {
            "user_id": str(user_id),
            "payment_type": "questions",
            "quantity": quantity,
            "internal_id": payment_id
        }
    })

    confirm_url = payment.confirmation.confirmation_url
    await call.message.answer(
        f"🧾 <b>Оплата</b>\n\n"
        f"Ты выбрал {quantity} вопрос(ов) за {amount}₽.\n"
        f"Перейди по ссылке, чтобы оплатить:\n\n"
        f"<a href='{confirm_url}'>💳 Оплатить через YooKassa</a>",
        disable_web_page_preview=True
    )
