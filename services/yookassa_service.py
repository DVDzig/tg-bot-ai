import base64
import requests
import uuid
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

def create_payment(amount_rub: int, description: str, user_id: int, questions: int, status: str = None):
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
            "questions": str(questions),
            "status": status or "none"
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
