import base64
import requests
import uuid
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

def create_payment(amount_rub: int, description: str, user_id: int, questions: int):
    auth_string = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
    auth_encoded = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_encoded}",
        "Content-Type": "application/json",
        "Idempotence-Key": str(uuid.uuid4())
    }

    data = {
        "amount": {
            "value": f"{amount_rub:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/tg_bot_ai_bot"  # можешь заменить на свой
        },
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            "questions": str(questions)
        },
        "capture": True
    }

    response = requests.post("https://api.yookassa.ru/v3/payments", headers=headers, json=data)
    result = response.json()

    if "confirmation" in result:
        return result["confirmation"]["confirmation_url"]
    else:
        print("❌ Ошибка при создании платежа:", result)
        return None
