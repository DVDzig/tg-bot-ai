import uuid
from yookassa import Configuration, Payment
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY


async def create_yookassa_payment(user_id: int, amount: int, description: str, payment_type: str, quantity: int) -> str:
    internal_id = str(uuid.uuid4())

    payment = Payment.create({
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/TGTutorBot"
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": str(user_id),
            "payment_type": payment_type,
            "quantity": quantity,
            "internal_id": internal_id
        },
        "receipt": {
            "customer": {
                "full_name": "Telegram User",
                "email": "example@example.com"  # Для тестов можно использовать email-заглушку
            },
            "items": [
                {
                    "description": description,
                    "quantity": "1.00",
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency": "RUB"
                    },
                    "vat_code": 1
                }
            ]
        }
    })

    return payment.confirmation.confirmation_url, internal_id
