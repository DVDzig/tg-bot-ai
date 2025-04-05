from fastapi import APIRouter, Request
from services.user_service import update_user_subscription

router = APIRouter()

@router.post("/yookassa-webhook")
async def yookassa_webhook(request: Request):
    data = await request.json()

    # Проверяем, что платёж был успешным
    if data["object"]["status"] == "succeeded":
        user_id = data["object"]["metadata"]["user_id"]
        # Обновляем подписку пользователя
        await update_user_subscription(user_id, "pro")  # Здесь "pro" может быть "lite", "pro" и т.д.
        return {"status": "success"}

    return {"status": "failed"}
