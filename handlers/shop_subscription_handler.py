import uuid
import requests
from aiogram import Router, F
from aiogram.types import CallbackQuery
from yookassa import Payment

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from keyboards.shop import get_subscription_packages_keyboard
from services.payment_service import log_pending_payment

router = Router()

import yookassa
yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY


@router.callback_query(F.data == "shop_subscription")
async def show_subscriptions(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "💳 <b>Подписки</b>\n\n"
        "🔓 <b>Лайт</b> — 7 дней безлимита. Идеально, если хочешь прокачаться за неделю. XP не начисляется.\n"
        "🔓 <b>Про</b> — максимум: безлимит, +100 вопросов, видео, приоритет, генерация изображений.\n\n"
        "Выбери подписку, чтобы оформить:",
        reply_markup=get_subscription_packages_keyboard()
    )


@router.callback_query(F.data.startswith("buy_sub_"))
async def handle_buy_subscription(call: CallbackQuery):
    await call.answer()

    sub_type = call.data.replace("buy_sub_", "")
    user_id = call.from_user.id

    if sub_type == "lite":
        amount = 149
        days = 7
    elif sub_type == "pro":
        amount = 499
        days = 30
    else:
        await call.message.answer("Ошибка: неизвестный тариф.")
        return

    internal_id = str(uuid.uuid4())

    await log_pending_payment(user_id, internal_id, days, sub_type)

    payment = Payment.create({
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/YourBotUsername"  # заменить на имя бота
        },
        "capture": True,
        "description": f"{sub_type} подписка для user_id {user_id}",
        "metadata": {
            "user_id": str(user_id),
            "payment_type": "subscription",
            "quantity": days,
            "internal_id": internal_id,
            "subscription_type": sub_type
        }
    })

    confirm_url = payment.confirmation.confirmation_url
    await call.message.answer(
        f"💳 <b>Оплата</b>\n\n"
        f"Ты выбрал подписку <b>{sub_type.upper()}</b> за {amount}₽.\n"
        f"Перейди по ссылке, чтобы оплатить:\n\n"
        f"<a href='{confirm_url}'>💳 Оплатить через YooKassa</a>",
        disable_web_page_preview=True
    )



def generate_payment_link(amount: float, description: str, user_id: int) -> str:
    url = "https://api.yookassa.ru/v3/labels"
    
    headers = {
        "Authorization": f"Bearer {YOOKASSA_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "amount": {
            "value": amount,
            "currency": "RUB"
        },
        "capture_mode": "AUTOMATIC",
        "description": description,
        "metadata": {
            "user_id": user_id
        }
    }

    # Отправляем запрос для генерации ссылки
    response = requests.post(url, json=data, headers=headers)
    
    # Обработка ответа
    if response.status_code == 200:
        response_data = response.json()
        return response_data["confirmation"]["confirmation_url"]
    else:
        raise Exception("Ошибка при генерации платёжной ссылки")
