import os

# Telegram и OpenAI
TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google Sheets
USER_SHEET_ID = os.getenv("USER_SHEET_ID")
USER_SHEET_NAME = os.getenv("USER_SHEET_NAME", "Users")
PROGRAM_SHEETS = os.getenv("PROGRAM_SHEETS")
client_email = os.getenv("CLIENT_EMAIL")

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
print(f"[CONFIG] 🧩 PROGRAM_SHEETS_LIST: {PROGRAM_SHEETS_LIST}")

# Поля для пользователей (в Google Таблице)
USER_FIELDS = [
    "user_id", "username", "first_name", "last_name", "language_code", "is_premium",
    "first_interaction", "last_interaction",
    "question_count", "day_count", "status", "plan",
    "discipline", "module", "xp", "xp_today", "xp_week",
    "paid_questions", "last_free_reset", "free_questions", "last_bonus_date",
    "premium_status", "premium_until", "last_daily_challenge", "last_thematic_challenge",
    "last_daily_3", "last_multi_disc",
    "last_weekly_10", "last_weekly_50xp", "last_weekly_5disc", "last_streak3", "xp_start_of_week", 
    "streak_days", "last_streak_date", "last_xp_bonus",
    "missions_streak", "last_mission_day"
]

ADMIN_ID = os.getenv("ADMIN_ID")

VIDEO_URLS = {
    "Профи": 1,
    "Эксперт": 2,
    "Наставник": 3,
    "Легенда": 3,
    "Создатель": 3,
    "lite": 3,
    "pro": 3,
}

