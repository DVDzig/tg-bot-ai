from config import PAYMENT_LOG_SHEET
from services.google_sheets_service import append_row_to_sheet
from datetime import datetime
import pytz


async def log_pending_payment(user_id: int, payment_type: str, amount: int, internal_id: str):
    """
    Логируем создание платежа в таблицу (до подтверждения)
    """
    timestamp = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")

    await append_row_to_sheet(PAYMENT_LOG_SHEET, [
        timestamp,
        str(user_id),
        payment_type,
        str(amount),
        internal_id,
        "pending"
    ])
