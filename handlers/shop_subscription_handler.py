import uuid
import requests
import yookassa
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from services.yookassa_service import Payment

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from keyboards.shop import get_subscription_packages_keyboard
from services.payment_service import log_pending_payment

router = Router()

yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY


@router.message(F.text == "💼 Подписки")
async def shop_subscription_entry_point(message: Message):
    await call.answer(
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



