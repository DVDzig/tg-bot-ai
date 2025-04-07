from aiogram import Router, F
from aiogram.types import Message
from config import USER_SHEET_ID
from services.sheets import get_sheets_service
from services.yookassa_service import Payment
from services.payment_service import log_pending_payment
from datetime import datetime
from services.google_sheets_service import append_payment_log


router = Router()

async def log_payment_to_sheet(user_id: int, payment_id: str, quantity: int, payment_type: str):
    SHEET_NAME = "PaymentsLog"
    service = get_sheets_service()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        str(user_id),
        str(quantity),
        str(payment_type),
        "pending",
        "payment",
        payment_id,
        timestamp
    ]
    body = {"values": [row]}
    service.spreadsheets().values().append(
        spreadsheetId=USER_SHEET_ID,
        range=f"{SHEET_NAME}!A:G",
        valueInputOption="RAW",
        body=body
    ).execute()


async def create_payment_and_send(message: Message, amount: int, description: str, payment_type: str):
    user_id = message.from_user.id
    try:
        payment = Payment.create({
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/your_bot_username"
            },
            "capture": True,
            "description": f"{description} ({user_id})",
            "metadata": {
                "user_id": str(user_id),
                "type": payment_type
            }
        })
        payment_url = payment.confirmation.confirmation_url
        payment_id = payment.id

        await log_pending_payment(user_id, payment_type, amount, payment_id)
        await message.answer(f"Перейди по ссылке для оплаты: {payment_url}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")


@router.message(F.text == "💳 Подписка Лайт (7 дней)")
async def handle_light_subscription_payment(message: Message):
    await create_payment_and_send(message, amount=149, description="Подписка Лайт (7 дней)", payment_type="subscription_lite")


@router.message(F.text == "💳 Подписка Про")
async def handle_pro_subscription_payment(message: Message):
    await create_payment_and_send(message, amount=299, description="Подписка Про", payment_type="subscription_pro")


@router.message(F.text == "💳 Купить 1 вопрос")
async def handle_single_question_purchase(message: Message):
    await create_payment_and_send(message, amount=10, description="Покупка 1 вопроса", payment_type="questions_1")


@router.message(F.text == "💳 Купить 10 вопросов")
async def handle_ten_questions_purchase(message: Message):
    await create_payment_and_send(message, amount=90, description="Покупка 10 вопросов", payment_type="questions_10")


@router.message(F.text == "💳 Купить 50 вопросов")
async def handle_fifty_questions_purchase(message: Message):
    await create_payment_and_send(message, amount=450, description="Покупка 50 вопросов", payment_type="questions_50")


@router.message(F.text == "💳 Купить 100 вопросов")
async def handle_hundred_questions_purchase(message: Message):
    await create_payment_and_send(message, amount=900, description="Покупка 100 вопросов", payment_type="questions_100")

async def log_successful_payment(user_id: int, quantity: int, payment_type: str, payment_id: str):
    # Логируем успешный платёж
    row = [
        str(user_id),
        payment_id,
        payment_type,
        quantity,
        "success"
    ]
    await append_payment_log(row)
