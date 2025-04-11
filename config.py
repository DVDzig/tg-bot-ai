import os

# Telegram и OpenAI
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google Sheets
USER_SHEET_ID = os.getenv("USER_SHEET_ID")
USER_SHEET_NAME = os.getenv("USER_SHEET_NAME","Users")
PROGRAM_SHEETS = os.getenv("PROGRAM_SHEETS")
client_email = os.getenv("CLIENT_EMAIL")
PAYMENT_LOG_SHEET = "PaymentsLog"

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Статусы, для которых генерируются NFT
NFT_STATUSES = ["Наставник", "Легенда", "Создатель"]

# Папка на Google Диске
NFT_FOLDER_ID = os.getenv("NFT_FOLDER_ID")


# Yookassa
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# YouTube API
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Названия листов с образовательными программами
PROGRAM_SHEETS_LIST = {
    'МРК': os.getenv("SHEET_PLAN_MRK", "ПланМРК"),
    'ТПР': os.getenv("SHEET_PLAN_TPR", "ПланТПР"),
    'БХ': os.getenv("SHEET_PLAN_BH", "ПланБХ"),
    'ФВМ': os.getenv("SHEET_PLAN_FVM", "ПланФВМ"),
    'СА': os.getenv("SHEET_PLAN_SA", "ПланСА"),
    'МСС': os.getenv("SHEET_PLAN_MSS", "ПланМСС")
}
# Поля для пользователей (в Google Таблице)
USER_FIELDS = [
    "user_id", "username", "first_name", "last_name", 
    "language_code", "is_premium",
    "first_interaction", "last_interaction",
    "question_count", "day_count", "status", "xp", "xp_week", 
    "paid_questions", "last_free_reset", "free_questions", "streak_days",
    "daily_mission_done", "weekly_mission_done", "streak_mission_done",
    "premium_status", "Ежедневная миссия", "Недельная миссия", 
    "Стрик-миссия", "plan", "premium_status", "premium_until", 
    "next_plan", "next_until", "nft_statuses", "nft_url_Наставник", 
    "nft_url_Легенда", "nft_url_Создатель"
]


ADMIN_ID = int(os.getenv("ADMIN_ID", "150532949"))

VIDEO_URLS = {
    "Профи": 1,
    "Эксперт": 2,
    "Наставник": 3,
    "Легенда": 3,
    "Создатель": 3,
    "lite": 3,
    "pro": 3,
}