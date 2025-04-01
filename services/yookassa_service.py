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

    receipt = {
        "customer": {
            "full_name": f"Пользователь {user_id}",  # можно заменить, если есть имя
            "email": f"user{user_id}@noemail.bot"    # подставной email (если нет реального)
        },
        "items": [{
            "description": description,
            "quantity": "1.00",
            "amount": {
                "value": f"{amount_rub:.2f}",
                "currency": "RUB"
            },
            "vat_code": 1  # без НДС
        }]
    }

    data = {
        "amount": {
            "value": f"{amount_rub:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/tg_bot_ai_bot"
        },
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            "questions": str(questions)
        },
        "capture": True,
        "receipt": receipt  # 👈 добавлен чек
    }

    response = requests.post("https://api.yookassa.ru/v3/payments", headers=headers, json=data)
    result = response.json()

    if "confirmation" in result:
        return result["confirmation"]["confirmation_url"]
    else:
        print("❌ Ошибка при создании платежа:", result)
        return None
