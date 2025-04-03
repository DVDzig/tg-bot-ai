from datetime import datetime, timedelta
from config import USER_SHEET_ID, USER_SHEET_NAME, PROGRAM_SHEETS, TOKEN
from .google_sheets_service import get_sheet_data, append_to_sheet, update_sheet_row, USER_FIELDS, pad_user_row
from aiogram import Bot
import asyncio
bot = Bot(token=TOKEN)

# Получение пользователя или регистрация
def get_or_create_user(user_id, username="Unknown", first_name="", last_name="", language_code="", is_premium=False):
    values = get_sheet_data(USER_SHEET_ID, f"{USER_SHEET_NAME}!A2:U")

    for idx, row in enumerate(values, start=2):
        if str(row[0]).strip() == str(user_id):
            row = pad_user_row(row)
            now = datetime.now().strftime("%d %B %Y, %H:%M")
            row[USER_FIELDS.index("last_interaction")] = now
            # Проверка просроченного платного статуса
            status_index = USER_FIELDS.index("premium_status")
            until_index = USER_FIELDS.index("premium_until")
            premium_status = row[status_index].strip().lower() if len(row) > status_index else ""
            premium_until = row[until_index].strip() if len(row) > until_index else ""

            if premium_status in ("light", "pro") and premium_until:
                try:
                    end_date = datetime.strptime(premium_until, "%Y-%m-%d").date()
                    today = datetime.now().date()
                    days_left = (end_date - today).days

                    # Статус истёк
                    if end_date < today:
                        row[status_index] = "none"
                        row[until_index] = ""
                        print(f"[INFO] Статус {premium_status} истёк у пользователя {user_id}")

                        # Отправка уведомления об отключении
                        asyncio.create_task(bot.send_message(
                            chat_id=int(user_id),
                            text=(
                                "⛔️ <b>Срок действия твоего статуса истёк</b>\n"
                                "Ты снова на базовом доступе.\n\n"
                                "💡 Хочешь продолжить без ограничений?\n"
                                "Попробуй <b>Лайт</b> или <b>Про</b> доступ 👉 «Купить доступ»"                                
                            ),
                            parse_mode="HTML"
                        ))

                    # Предупреждение за 1 день до окончания
                    elif days_left == 1:
                        asyncio.create_task(bot.send_message(
                            chat_id=int(user_id),
                            text=(
                                f"⏳ <b>Внимание!</b>\n"
                                f"Твой статус <b>{premium_status.capitalize()}</b> истекает завтра ({premium_until})!\n\n"
                                f"Если хочешь продлить — открой «Купить доступ» и выбери нужный вариант 🛒"
                            ),
                            parse_mode="HTML"
                        ))

                except Exception as e:
                    print(f"[ERROR] Ошибка при проверке статуса: {e}")

            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, idx, row)
            return row

    # Новый пользователь
    print(f"[INFO] Регистрируем нового пользователя {user_id}")
    return register_user(user_id, username, first_name, last_name, language_code, is_premium)


def register_user(user_id, username, first_name, last_name, language_code, is_premium):
    now = datetime.now()
    formatted_now = now.strftime("%d %B %Y, %H:%M")
    today_str = now.strftime("%d.%m.%Y")
    row_data = [
        str(user_id), username, first_name, last_name, language_code, str(is_premium),
        formatted_now, formatted_now,  # first_interaction, last_interaction
        "0", "0", "новичок", "", "", "", "0", "0", "0", "0", today_str, "10", ""
    ]
    append_to_sheet(USER_SHEET_ID, USER_SHEET_NAME, row_data)
    return row_data

def can_ask_question(user_id):
    user = get_or_create_user(user_id)
    free_q_index = USER_FIELDS.index("free_questions")
    paid_q_index = USER_FIELDS.index("paid_questions")
    free_questions = int(user[free_q_index]) if len(user) > free_q_index and user[free_q_index].isdigit() else 0
    paid_questions = int(user[paid_q_index]) if len(user) > paid_q_index and user[paid_q_index].isdigit() else 0
    return free_questions > 0 or paid_questions > 0

def determine_status(xp: int):
    thresholds = [
        ("новичок", 0),
        ("опытный", 11),
        ("профи", 51),
        ("эксперт", 151),
        ("наставник", 301),
        ("легенда", 1000),
        ("создатель", 5000),
    ]

    current = thresholds[0][0]
    next_status = thresholds[1][0]
    xp_to_next = thresholds[1][1] - xp

    for i in range(len(thresholds)):
        if xp >= thresholds[i][1]:
            current = thresholds[i][0]
            if i + 1 < len(thresholds):
                next_status = thresholds[i + 1][0]
                xp_to_next = thresholds[i + 1][1] - xp
            else:
                next_status = "максимальный"
                xp_to_next = 0

    return current, next_status, max(0, xp_to_next)


def decrement_question_balance(user_id):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    free_q_index = USER_FIELDS.index("free_questions")
    paid_q_index = USER_FIELDS.index("paid_questions")

    for idx, row in enumerate(values, start=2):
        if str(row[0]) == str(user_id):
            row = pad_user_row(row)


            free_q = int(row[free_q_index]) if row[free_q_index].isdigit() else 0
            paid_q = int(row[paid_q_index]) if row[paid_q_index].isdigit() else 0

            if free_q > 0:
                free_q -= 1
                row[free_q_index] = str(free_q)
            elif paid_q > 0:
                paid_q -= 1
                row[paid_q_index] = str(paid_q)
            else:
                return False

            update_sheet_row(USER_SHEET_ID, "Users", idx, row)
            return True

    return False

def update_user_xp(user_id, xp_gain=1):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    xp_index = USER_FIELDS.index("xp")
    status_index = USER_FIELDS.index("status")
    premium_index = USER_FIELDS.index("premium_status")

    for i, row in enumerate(values, start=2):
        if row[0] == str(user_id):
            row = pad_user_row(row)


            # 🛡 Проверка подписки
            premium_status = row[premium_index].strip().lower()
            if premium_status in ("light", "pro"):
                return int(row[xp_index]) if row[xp_index].isdigit() else 0, row[status_index]

            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + xp_gain
            status, _, _ = determine_status(new_xp)
            print(f"[XP UPDATE] user {user_id} → XP: {new_xp}, status: {status}")

            row[xp_index] = str(new_xp)
            row[status_index] = status

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return new_xp, status

    return 0, "новичок"


def get_user_profile(user_id):
    user = get_or_create_user(user_id)
    profile = {}
    for field in USER_FIELDS:
        index = USER_FIELDS.index(field)
        value = user[index] if len(user) > index else ""
        if field in ["xp", "free_questions", "paid_questions"]:
            profile[field] = int(value) if str(value).isdigit() else 0
        else:
            profile[field] = value
    return profile

def apply_xp_penalty_if_needed(user_id):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    xp_index = USER_FIELDS.index("xp")
    status_index = USER_FIELDS.index("status")
    last_interaction_index = USER_FIELDS.index("last_interaction")

    for i, row in enumerate(values, start=2):
        if str(row[0]) == str(user_id):
            row = pad_user_row(row)

            last_interaction = row[last_interaction_index]
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0

            try:
                last_date = datetime.strptime(last_interaction, "%d %B %Y, %H:%M")
            except ValueError:
                return

            days_inactive = (datetime.now() - last_date).days
            penalty = 5 if 5 <= days_inactive < 10 else 10 if days_inactive >= 10 else 0

            if penalty > 0:
                new_xp = max(xp - penalty, 0)
                status, _, _ = determine_status(new_xp)

                row[xp_index] = str(new_xp)
                row[status_index] = status
                update_sheet_row(USER_SHEET_ID, "Users", i, row)
            break

def get_user_activity_stats(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    total = 0
    today_count = 0
    week_count = 0

    for row in qa_log:
        if len(row) < 2 or row[0] != str(user_id):
            continue
        try:
            ts = datetime.strptime(row[1], "%d %B %Y, %H:%M")
        except:
            continue

        total += 1
        if ts.date() == today:
            today_count += 1
        if ts.date() >= week_ago:
            week_count += 1

    return {
        "total": total,
        "today": today_count,
        "week": week_count
    }

def check_and_apply_daily_challenge(user_id):
    from config import PROGRAM_SHEETS
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    today_str = datetime.now().strftime("%d.%m.%Y")

    xp_index = USER_FIELDS.index("xp")
    status_index = USER_FIELDS.index("status")
    free_q_index = USER_FIELDS.index("free_questions")
    daily_challenge_index = USER_FIELDS.index("last_daily_challenge")  # новое поле!

    for idx, row in enumerate(values, start=2):
        if str(row[0]) != str(user_id):
            continue

        row = pad_user_row(row)


        last_done = row[daily_challenge_index] if row[daily_challenge_index] else ""
        if last_done == today_str:
            return False  # Бонус уже был сегодня

        today_count = 0
        for qa in qa_log:
            if str(qa[0]) == str(user_id):
                try:
                    ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                    if ts.date() == datetime.now().date():
                        today_count += 1
                except:
                    continue

        if today_count >= 3:
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 2
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[daily_challenge_index] = today_str  # сохраняем дату выполнения

            update_sheet_row(USER_SHEET_ID, "Users", idx, row)
            return True

    return False

def add_paid_questions(user_id: int, count: int):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    paid_q_index = USER_FIELDS.index("paid_questions")

    for idx, row in enumerate(values, start=2):
        if str(row[0]) == str(user_id):
            row = pad_user_row(row)


            current = int(row[paid_q_index]) if row[paid_q_index].isdigit() else 0
            row[paid_q_index] = str(current + count)

            update_sheet_row(USER_SHEET_ID, "Users", idx, row)
            return True

    return False

def update_user_data(user_id: int, updates: dict):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    
    for idx, row in enumerate(values, start=2):
        if str(row[0]) == str(user_id):
            row = pad_user_row(row)


            for key, value in updates.items():
                if key in USER_FIELDS:
                    row[USER_FIELDS.index(key)] = value

            update_sheet_row(USER_SHEET_ID, "Users", idx, row)
            return True

    return False

def refresh_monthly_free_questions():
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    status_index = USER_FIELDS.index("status")
    free_index = USER_FIELDS.index("free_questions")

    bonus_by_status = {
        "новичок": 5,
        "опытный": 10,
        "профи": 20,
        "эксперт": 30,
        "наставник": 50,
        "легенда": 75,
        "создатель": 100
    }

    for i, row in enumerate(values, start=2):
        row = pad_user_row(row)


        status = row[status_index].strip().lower()
        current_free = int(row[free_index]) if row[free_index].isdigit() else 0
        bonus = bonus_by_status.get(status, 5)
        updated = current_free + bonus

        row[free_index] = str(updated)
        update_sheet_row(USER_SHEET_ID, "Users", i, row)

def check_thematic_challenge(user_id):
    from config import PROGRAM_SHEETS
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")

    today = datetime.now().date()
    today_str = datetime.now().strftime("%d.%m.%Y")

    discipline_set = set()
    thematic_index = USER_FIELDS.index("last_thematic_challenge")
    xp_index = USER_FIELDS.index("xp")
    status_index = USER_FIELDS.index("status")

    for i, row in enumerate(values, start=2):
        if str(row[0]) != str(user_id):
            continue

        row = pad_user_row(row)


        last_done = row[thematic_index] if row[thematic_index] else ""
        if last_done == today_str:
            return False  # Уже выполнено сегодня

        # Подсчёт уникальных дисциплин за сегодня
        for qa in qa_log:
            if str(qa[0]) == str(user_id):
                try:
                    ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                    if ts.date() == today:
                        discipline = qa[4].strip().lower()
                        if discipline:
                            discipline_set.add(discipline)
                except:
                    continue

        if len(discipline_set) >= 3:
            # ✅ Выполнил миссию
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 5
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[thematic_index] = today_str
            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return True

    return False
