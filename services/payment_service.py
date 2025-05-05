from datetime import datetime
from config import USER_SHEET_ID
from services.sheets import get_sheets_service

# Название листа в таблице пользователей
SHEET_NAME = "PaymentsLog"

# Логирование ожидающего платежа
async def log_pending_payment(user_id: int, payment_id: str, quantity: int, payment_type: str):
    timestamp = datetime.utcnow().strftime("%d %B %Y, %H:%M")
    row = [
        str(user_id),
        str(quantity),
        str(payment_type),
        "pending",     # статус
        "payment",     # тип события
        payment_id,
        timestamp
    ]

    service = get_sheets_service()
    sheet = service.spreadsheets().values()
    sheet.append(
        spreadsheetId=USER_SHEET_ID,
        range=f"{SHEET_NAME}!A:G",
        valueInputOption="RAW",
        body={"values": [row]}
    ).execute()

# Логирование успешного платежа (по необходимости)
async def log_successful_payment(user_id: int, payment_id: str):
    timestamp = datetime.utcnow().strftime("%d %B %Y, %H:%M")
    row = [
        str(user_id),
        "",                   # quantity
        "",                   # type
        "success",
        "payment",
        payment_id,
        timestamp
    ]

    service = get_sheets_service()
    sheet = service.spreadsheets().values()
    sheet.append(
        spreadsheetId=USER_SHEET_ID,
        range=f"{SHEET_NAME}!A:G",
        valueInputOption="RAW",
        body={"values": [row]}
    ).execute()
