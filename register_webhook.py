import base64
import requests
import uuid

# === Данные YooKassa ===
shop_id = "1059797"
secret_key = "live_oRsbsdcpTtq0lIPiq4X_JddZYvMdGii7-VCwT4NsMIY"
webhook_url = "https://tg-bot-ai-teyr.onrender.com/payment/result"

# === Basic Auth
auth_string = f"{shop_id}:{secret_key}"
auth_bytes = auth_string.encode("utf-8")
auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/json",
    "Idempotence-Key": str(uuid.uuid4())
}

data = {
    "event": "payment.succeeded",
    "url": webhook_url
}

response = requests.post("https://api.yookassa.ru/v3/webhooks", headers=headers, json=data)

print("Status Code:", response.status_code)
print("Response:", response.text)
