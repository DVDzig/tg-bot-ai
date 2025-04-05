from fastapi import APIRouter, Request
from services.user_service import update_user_subscription, add_paid_questions
from services.payment_service import log_successful_payment
from config import YOOKASSA_SECRET_KEY

router = APIRouter()

@router.post("/yookassa-webhook")
async def yookassa_webhook(request: Request):
    # Получаем данные из webhook
    data = await request.json()

    # Проверка, что платёж прошёл успешно
    if data["object"]["status"] == "succeeded":
        payment_id = data["object"]["id"]
        user_id = data["object"]["metadata"]["user_id"]
        payment_type = data["object"]["metadata"]["payment_type"]
        quantity = int(data["object"]["amount"]["value"])

        # Логируем успешный платёж
        await log_successful_payment(user_id, quantity, payment_type, payment_id)

        # Обновляем данные пользователя в зависимости от типа платежа
        if payment_type == "questions":
            await add_paid_questions(user_id, quantity)  # Добавляем оплаченные вопросы
        elif payment_type == "subscription":
            # Обновляем подписку пользователя
            if data["object"]["metadata"]["plan"] == "pro":
                await update_user_subscription(user_id, "pro")  # Активируем подписку Про
            elif data["object"]["metadata"]["plan"] == "lite":
                await update_user_subscription(user_id, "lite")  # Активируем подписку Лайт

        return {"status": "success"}
    
    return {"status": "failed"}