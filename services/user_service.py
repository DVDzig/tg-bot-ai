from datetime import datetime, timedelta
from config import USER_SHEET_ID, USER_SHEET_NAME, PROGRAM_SHEETS, TOKEN, USER_FIELDS
from services.google_sheets_service import get_sheet_data, append_to_sheet, update_sheet_row, pad_user_row, UserRow
from services.user_helpers import get_user_row, set_user_cache
from aiogram import Bot
from services.missions import update_activity_rewards, determine_status
import asyncio
bot = Bot(token=TOKEN)

# Получение пользователя или регистрация
def get_or_create_user(user_id, username="Unknown", first_name="", last_name="", language_code="", is_premium=False):
    i, row = get_user_row(user_id)
    if row:
        user = UserRow(row)
        user.set("last_interaction", datetime.now().strftime("%d %B %Y, %H:%M"))

        premium_status = user.get("premium_status").strip().lower()
        premium_until = user.get("premium_until").strip()

        if premium_status in ("light", "pro") and premium_until:
            try:
                end_date = datetime.strptime(premium_until, "%Y-%m-%d").date()
                today = datetime.now().date()
                days_left = (end_date - today).days

                if end_date < today:
                    user.set("premium_status", "none")
                    user.set("premium_until", "")
                    asyncio.create_task(
                        bot.send_message(
                            chat_id=user_id,
                            text=(
                                "⛔️ <b>Срок действия твоего статуса истёк</b>\n"
                                "Ты снова на базовом доступе.\n\n"
                                "💡 Хочешь продолжить без ограничений?\n"
                                "Попробуй <b>Лайт</b> или <b>Про</b> доступ 👉 «Купить доступ»"
                            ),
                            parse_mode="HTML"
                        )
                    )
                elif days_left == 1:
                    asyncio.create_task(
                        bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"⏳ <b>Внимание!</b>\n"
                                f"Твой статус <b>{premium_status.capitalize()}</b> истекает завтра ({premium_until})!\n\n"
                                f"Если хочешь продлить — открой «Купить доступ» и выбери нужный вариант 🛒"
                            ),
                            parse_mode="HTML"
                        )
                    )
            except Exception as e:
                print(f"[ERROR] Ошибка проверки подписки: {e}")

        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, user.data())

        set_user_cache(user_id, (i, user.data()))
        return user.data()
    
    # Повторно проверим через get_user_row — даже если кеш был пуст
    j, duplicate_row = get_user_row(user_id)
    if duplicate_row:
        print(f"[WARN] Повторная регистрация пользователя {user_id} заблокирована")
        user = UserRow(duplicate_row)
        user.set("last_interaction", datetime.now().strftime("%d %B %Y, %H:%M"))
        if j is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, j, user.data())
        set_user_cache(user_id, (j, user.data()))
        return user.data()

    # 👉 Если действительно нет пользователя — регистрируем нового
    print(f"[INFO] Регистрируем нового пользователя {user_id}")
    new_user = register_user(user_id, username, first_name, last_name, language_code, is_premium)
    set_user_cache(user_id, (None, new_user))
    return new_user

def register_user(user_id, username, first_name, last_name, language_code, is_premium):
    now = datetime.now()
    formatted_now = now.strftime("%d %B %Y, %H:%M")
    today_str = now.strftime("%d.%m.%Y")

    row_data = [
        str(user_id), username, first_name, last_name, language_code, str(is_premium),
        formatted_now, formatted_now,  # first_interaction, last_interaction
        "0", "0", "новичок", "", "", "", "0", "0", "0", "0", today_str, "10", "",
        "none", "", "", "", "", "", "", "", "", "", "", "", ""
    ]

    # Заполним до длины USER_FIELDS
    if len(row_data) < len(USER_FIELDS):
        row_data += [""] * (len(USER_FIELDS) - len(row_data))

    append_to_sheet(USER_SHEET_ID, USER_SHEET_NAME, row_data)
    return row_data

def can_ask_question(user_id: int) -> bool:
    user = UserRow(user_id)
    return user.get("free_questions", 0) > 0 or user.get("paid_questions", 0) > 0

def decrement_question_balance(user_id: int) -> bool:
    user = UserRow(user_id)
    free = user.get("free_questions", 0)
    paid = user.get("paid_questions", 0)

    if free > 0:
        user.set("free_questions", free - 1)
    elif paid > 0:
        user.set("paid_questions", paid - 1)
    else:
        return False

    user.save()
    return True

def update_user_xp(user_id, xp_gain=1):
    i, row = get_user_row(user_id)
    if not row:
        return 0, "новичок"

    user = UserRow(row)

    if user.get("premium_status").lower() in ("light", "pro"):
        return user.get_int("xp"), user.get("status")

    user.add_to_int("xp", xp_gain)
    new_status, _, _ = determine_status(user.get_int("xp"))
    user.set("status", new_status)

    if i is not None:
        update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, user.data())

    set_user_cache(user_id, (i, user.data()))

    update_activity_rewards(user_id)  # 🧩 вызываем после обновления XP

    return user.get_int("xp"), new_status

def get_user_profile(user_id):
    _, row = get_user_row(user_id)
    if not row:
        return {}

    profile = {}
    for i, field in enumerate(USER_FIELDS):
        value = row[i] if i < len(row) else ""
        if field in ["xp", "free_questions", "paid_questions"]:
            profile[field] = int(value) if str(value).isdigit() else 0
        else:
            profile[field] = value
    return profile

def apply_xp_penalty_if_needed(user_id):
    i, row = get_user_row(user_id)
    if not row:
        return

    last_index = USER_FIELDS.index("last_interaction")
    xp_index = USER_FIELDS.index("xp")
    status_index = USER_FIELDS.index("status")

    try:
        last_date = datetime.strptime(row[last_index], "%d %B %Y, %H:%M")
        days_inactive = (datetime.now() - last_date).days
    except:
        return

    penalty = 5 if 5 <= days_inactive < 10 else 10 if days_inactive >= 10 else 0
    if penalty == 0:
        return

    xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
    new_xp = max(xp - penalty, 0)
    new_status, _, _ = determine_status(new_xp)

    row[xp_index] = str(new_xp)
    row[status_index] = new_status

    if i is not None:
        update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

    set_user_cache(user_id, (i, row))


def get_user_activity_stats(user_id):
    try:
        qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    except Exception as e:
        print(f"[ERROR] Не удалось получить QA_Log: {e}")
        return {
            "total": 0,
            "today": 0,
            "week": 0
        }

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    total = today_count = week_count = 0

    for row in qa_log:
        if len(row) < 2 or str(row[0]) != str(user_id):
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

def check_and_apply_daily_challenge(user_id: int) -> bool:
    from services.google_sheets_service import get_sheet_data
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    today = datetime.now().date()
    today_str = today.strftime("%d.%m.%Y")

    user = UserRow(user_id)
    if user.get("last_daily_challenge") == today_str:
        return False

    count = 0
    for qa in qa_log:
        if str(qa[0]) == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                if ts.date() == today:
                    count += 1
            except:
                continue

    if count >= 3:
        xp = user.get("xp", 0) + 2
        user.set("xp", xp)
        user.set("status", determine_status(xp)[0])
        user.set("last_daily_challenge", today_str)
        user.save()
        return True

    return False

def add_paid_questions(user_id: int, count: int) -> bool:
    i, row = get_user_row(user_id)
    if not row:
        return False
    user = UserRow(row)
    current = user.get("paid_questions", 0)
    user.set("paid_questions", current + count)
    if i is not None:
        update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, user.data())
        set_user_cache(user_id, (i, user.data()))
        return True
    return False

def update_user_data(user_id: int, updates: dict) -> bool:
    i, row = get_user_row(user_id)
    if not row:
        return False
    user = UserRow(row)
    for key, value in updates.items():
        user.set(key, value)
    if i is not None:
        update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, user.data())
        set_user_cache(user_id, (i, user.data()))
        return True
    return False

def refresh_monthly_free_questions():
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")

    bonus_by_status = {
        "новичок": 5, "опытный": 10, "профи": 20,
        "эксперт": 30, "наставник": 50,
        "легенда": 75, "создатель": 100
    }

    for i, row in enumerate(values, start=2):
        row = pad_user_row(row)
        user_id = int(row[0])
        user = UserRow(user_id)
        status = user.get("status", "новичок").strip().lower()
        bonus = bonus_by_status.get(status, 5)
        user.set("free_questions", user.get("free_questions", 0) + bonus)
        user.save()

def check_thematic_challenge(user_id: int) -> bool:
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    today = datetime.now().date()
    today_str = today.strftime("%d.%m.%Y")

    user = UserRow(user_id)
    if user.get("last_thematic_challenge") == today_str:
        return False

    disciplines = set()
    for qa in qa_log:
        if str(qa[0]) == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                if ts.date() == today and len(qa) > 4:
                    disciplines.add(qa[4].strip().lower())
            except:
                continue

    if len(disciplines) >= 3:
        xp = user.get("xp", 0) + 5
        user.set("xp", xp)
        user.set("status", determine_status(xp)[0])
        user.set("last_thematic_challenge", today_str)
        user.save()
        return True

    return False

