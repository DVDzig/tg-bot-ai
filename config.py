import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv("TOKEN")
USER_SHEET_ID = os.getenv("USER_SHEET_ID")
USER_SHEET_NAME = os.getenv("USER_SHEET_NAME", "Users")
client_email = os.getenv("CLIENT_EMAIL")
PROGRAM_SHEETS = os.getenv("PROGRAM_SHEETS")

PROGRAM_SHEETS_LIST = {
    'МРК': os.getenv("SHEET_PLAN_MRK", "ПланМРК"),
    'ТПР': os.getenv("SHEET_PLAN_TPR", "ПланТПР"),
    'БХ': os.getenv("SHEET_PLAN_BH", "ПланБХ")
}

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

robokassa_links = {
    "1 вопрос – 10₽": 10,
    "10 вопросов – 90₽": 90,
    "20 вопросов – 180₽": 180,
    "50 вопросов – 450₽": 450,
    "100 вопросов – 900₽": 900,
}

ROBOKASSA_LOGIN = os.getenv("ROBOKASSA_LOGIN")
ROBOKASSA_PASSWORD1 = os.getenv("ROBOKASSA_PASSWORD1")
ROBOKASSA_URL = os.getenv("ROBOKASSA_URL")
