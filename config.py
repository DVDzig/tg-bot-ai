import os

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv("TOKEN")
USER_SHEET_ID = os.getenv("USER_SHEET_ID")
USER_SHEET_NAME = os.getenv("USER_SHEET_NAME", "Users")
client_email = os.getenv("CLIENT_EMAIL")
PROGRAM_SHEETS = os.getenv("PROGRAM_SHEETS")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")


PROGRAM_SHEETS_LIST = {
    'МРК': os.getenv("SHEET_PLAN_MRK", "ПланМРК"),
    'ТПР': os.getenv("SHEET_PLAN_TPR", "ПланТПР"),
    'БХ': os.getenv("SHEET_PLAN_BH", "ПланБХ"),
    'ФВМ': os.getenv("SHEET_PLAN_FVM", "ПланФВМ"),
    'СА': os.getenv("SHEET_PLAN_SA", "ПланСА"),
    'МСС': os.getenv("SHEET_PLAN_MSS", "ПланМСС")
}


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

