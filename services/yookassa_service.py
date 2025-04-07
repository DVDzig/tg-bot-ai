import yookassa
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

yookassa.Configuration.account_id = YOOKASSA_SHOP_ID
yookassa.Configuration.secret_key = YOOKASSA_SECRET_KEY

class Payment:
    @staticmethod
    def create(data: dict):
        return yookassa.Payment.create(data)
