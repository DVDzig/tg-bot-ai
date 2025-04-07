from aiogram import Router, F
from aiogram.types import Message
from services.yookassa_service import Payment
from services.log_service import log_pending_payment
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
import yookassa
import uuid

router = Router()

# Настройка ключей YooKassa
yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY

# Подписка
@router.message(F.text == "💳 Подписка")
async def handle_subscription_payment(message: Message):
    user_id = message.from_user.id
    amount = 500
    description = "Подписка Лайт на 7 дней"
    payment_id = str(uuid.uuid4())

    await log_pending_payment(user_id, payment_id, 7, "subscription")

    payment = Payment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/TGTutorBot"
        },
        "capture": True,
        "description": f"Подписка Лайт (7 дней) для user_id {user_id}",
        "metadata": {
            "user_id": str(user_id),
            "payment_type": "subscription",
            "quantity": 7,
            "internal_id": payment_id
        }
    })

    confirm_url = payment.confirmation.confirmation_url
    await message.answer(
        f"🧾 <b>Подписка</b>\n\n"
        f"Ты выбрал подписку Лайт на 7 дней за {amount}₽.\n"
        f"Перейди по ссылке, чтобы оплатить:\n\n"
        f"<a href='{confirm_url}'>💳 Оплатить через YooKassa</a>",
        disable_web_page_preview=True
    )


# Покупка 1 вопроса
@router.message(F.text == "🟢 Купить 1 вопрос (10₽)")
async def buy_1_question(message: Message):
    await process_question_payment(message, 1, 10)

# Покупка 10 вопросов
@router.message(F.text == "🔹 Купить 10 вопросов (90₽)")
async def buy_10_questions(message: Message):
    await process_question_payment(message, 10, 90)

# Покупка 50 вопросов
@router.message(F.text == "🚀 Купить 50 вопросов (450₽)")
async def buy_50_questions(message: Message):
    await process_question_payment(message, 50, 450)

# Покупка 100 вопросов
@router.message(F.text == "👑 Купить 100 вопросов (900₽)")
async def buy_100_questions(message: Message):
    await process_question_payment(message, 100, 900)


# Общая функция оплаты вопросов
async def process_question_payment(message: Message, quantity: int, amount: int):
    user_id = message.from_user.id
    payment_id = str(uuid.uuid4())

    await log_pending_payment(user_id, payment_id, quantity, "questions")

    payment = Payment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/TGTutorBot"
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
    await message.answer(
        f"🧾 <b>Оплата</b>\n\n"
        f"Ты выбрал {quantity} вопрос(ов) за {amount}₽.\n"
        f"Перейди по ссылке, чтобы оплатить:\n\n"
        f"<a href='{confirm_url}'>💳 Оплатить через YooKassa</a>",
        disable_web_page_preview=True
    )
