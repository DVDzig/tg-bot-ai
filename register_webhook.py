import base64
import requests
import uuid

# === Данные YooKassa ===
shop_id = "1059797"
secret_key = "live_oRsbsdcpTtq0lIPiq4X_JddZYvMdGii7-VCwT4NsMIY"

# === Твой Render-домен
webhook_url = "https://tg-bot-ai-teyr.onrender.com/payment/result"

# === Авторизация ===
auth_token = base64.b64encode(f"{shop_id}:{secret_key}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth_token}",
    "Content-Type": "application/json",
    "Idempotence-Key": str(uuid.uuid4()),
}

# === Тело запроса ===
data = {
    "event": "payment.succeeded",
    "url": webhook_url
}

# === Отправка запроса ===
response = requests.post("https://api.yookassa.ru/v3/webhooks", headers=headers, json=data)

# === Ответ сервера ===
print("Status Code:", response.status_code)
print("Response:", response.text)
