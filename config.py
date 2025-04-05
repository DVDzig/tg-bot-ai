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
ADMIN_ID = os.getenv("YOOKASSA_SECRET_KEY")

PROGRAM_SHEETS_LIST = {
    'МРК': os.getenv("SHEET_PLAN_MRK", "ПланМРК"),
    'ТПР': os.getenv("SHEET_PLAN_TPR", "ПланТПР"),
    'БХ': os.getenv("SHEET_PLAN_BH", "ПланБХ"),
    'ФВМ': os.getenv("SHEET_PLAN_FVM", "ПланФВМ"),
    'СА': os.getenv("SHEET_PLAN_SA", "ПланСА"),
    'МСС': os.getenv("SHEET_PLAN_MSS", "ПланМСС")
}

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

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

VIDEO_URLS = {
    "МРК": {
        "Модуль 1": {
            "Дисциплина 1": [
                "https://link_to_video_1.com",
                "https://link_to_video_2.com",
                "https://link_to_video_3.com"
            ],
            "Дисциплина 2": [
                "https://link_to_video_4.com"
            ]
        }
    },
    "ТПР": {
        # Ссылки на видео для других программ
    }
}

