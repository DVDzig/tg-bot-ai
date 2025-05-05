from config import PAYMENT_LOG_SHEET
from services.google_sheets_service import append_payment_log
from datetime import datetime
import pytz


async def log_pending_payment(user_id: int, payment_type: str, amount: int, internal_id: str):
    """
    Логируем создание платежа в таблицу (до подтверждения)
    """
    timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%d %B %Y, %H:%M")

    await append_payment_log(PAYMENT_LOG_SHEET, [
        timestamp,
        str(user_id),
        payment_type,
        str(amount),
        internal_id,
        "pending"
    ])
