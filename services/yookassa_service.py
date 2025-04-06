import base64
import uuid
import requests
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

class Payment:
    def __init__(self, amount: float, description: str, user_id: int):
        self.amount = amount
        self.description = description
        self.user_id = user_id
        self.payment_url = None

def generate_payment_link(self) -> str:
    """
    Генерирует ссылку для оплаты через YooKassa.
    """
    url = "https://api.yookassa.ru/v3/labels"
    headers = {
        "Authorization": f"Bearer {YOOKASSA_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "amount": {
            "value": self.amount,
            "currency": "RUB"
        },
        "capture_mode": "AUTOMATIC",
        "description": self.description,
        "metadata": {
            "user_id": self.user_id
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        self.payment_url = response_data["confirmation"]["confirmation_url"]
        return self.payment_url
    else:
        raise Exception("Ошибка при генерации платёжной ссылки")

def get_payment_url(self) -> str:
    """
    Возвращает ссылку на страницу YooKassa для оплаты.
    """
    if not self.payment_url:
        raise ValueError("Ссылка на оплату не была сгенерирована. Пожалуйста, вызовите generate_payment_link() сначала.")
    return self.payment_url


# Функция для создания платёжной ссылки с использованием функции из Payment
def create_payment(amount_rub: int, description: str, user_id: int, questions: int, status: str = None):
    payment = Payment(amount=amount_rub, description=description, user_id=user_id)
    
    try:
        payment_url = payment.generate_payment_link()  # Используем метод класса Payment
        return payment_url
    except Exception as e:
        print(f"❌ Ошибка при создании платежа: {str(e)}")
        return None
