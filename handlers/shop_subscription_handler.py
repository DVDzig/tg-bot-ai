import uuid
import requests
import yookassa
from aiogram import Router, F
from aiogram.types import Message
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from services.yookassa_service import Payment
from services.log_service import log_pending_payment
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY


def get_subscription_selection_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔓 Лайт"), KeyboardButton(text="🔓 Про")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите подписку ⤵️"
    )


@router.message(F.text == "💼 Подписки")
async def shop_subscription_entry_point(message: Message):
    await message.answer(
        "💳 <b>Подписки</b>\n\n"
        "🔓 <b>Лайт</b> — 7 дней безлимита. Идеально, если хочешь прокачаться за неделю. XP не начисляется.\n"
        "🔓 <b>Про</b> — максимум: безлимит, +100 вопросов, видео, приоритет, генерация изображений.\n\n"
        "Выбери подписку, чтобы оформить:",
        reply_markup=get_subscription_selection_keyboard()
    )


@router.message(F.text.in_(["🔓 Лайт", "🔓 Про"]))
async def handle_buy_subscription(message: Message):
    sub_type = "lite" if "Лайт" in message.text else "pro"
    user_id = message.from_user.id

    if sub_type == "lite":
        amount = 149
        days = 7
    elif sub_type == "pro":
        amount = 499
        days = 30

    internal_id = str(uuid.uuid4())

    await log_pending_payment(user_id, internal_id, days, sub_type)

    payment = Payment.create({
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/TGTutorBot"  # Заменить на имя бота
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
    await message.answer(
        f"💳 <b>Оплата</b>\n\n"
        f"Ты выбрал подписку <b>{sub_type.upper()}</b> за {amount}₽.\n"
        f"Перейди по ссылке, чтобы оплатить:\n\n"
        f"<a href='{confirm_url}'>💳 Оплатить через YooKassa</a>",
        disable_web_page_preview=True
    )
