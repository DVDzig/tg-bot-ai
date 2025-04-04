from datetime import datetime, timedelta
from config import USER_SHEET_ID, PROGRAM_SHEETS, TOKEN, USER_FIELDS, USER_SHEET_NAME
from services.google_sheets_service import (
    get_sheet_data, update_sheet_row, pad_user_row
)
from services.user_helpers import get_user_row
 

class Mission:
    def __init__(self, id, title, type_, reward, check_fn):
        self.id = id
        self.title = title
        self.type = type_  # daily / weekly
        self.reward = reward
        self.check_fn = check_fn

    def check(self, user_id):
        return self.check_fn(user_id)

# 🔍 Вспомогательная функция

def get_index(field_name):
    return USER_FIELDS.index(field_name)

def update_activity_rewards(user_id):
    today = datetime.now().date()
    today_str = today.strftime("%d.%m.%Y")

    streak_index = get_index("streak_days")
    last_streak_index = get_index("last_streak_date")
    xp_index = get_index("xp")
    free_index = get_index("free_questions")
    bonus_index = get_index("last_xp_bonus")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    last_date_str = row[last_streak_index] if row[last_streak_index] else ""
    last_date = datetime.strptime(last_date_str, "%d.%m.%Y").date() if last_date_str else None

    # Обновление streak
    if last_date == today - timedelta(days=1):
        streak = int(row[streak_index]) + 1
    elif last_date == today:
        streak = int(row[streak_index])
    else:
        streak = 1

    row[streak_index] = str(streak)
    row[last_streak_index] = today_str

    # Бонусы за streak
    free = int(row[free_index]) if row[free_index].isdigit() else 0
    if streak == 7:
        free += 1
    elif streak == 14:
        free += 2

    # Бонусы за XP
    xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
    last_bonus = int(row[bonus_index]) if row[bonus_index].isdigit() else 0
    xp_bonus = 0
    for milestone in [100, 250, 500, 1000, 2000, 3000]:
        if last_bonus < milestone <= xp:
            xp_bonus += {100: 1, 250: 2, 500: 5, 1000: 5, 2000: 5, 3000: 5}[milestone]
            last_bonus = milestone

    if xp_bonus:
        free += xp_bonus

    row[free_index] = str(free)
    row[bonus_index] = str(last_bonus)

    if i is not None:
        update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

    return True

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

# ✅ 1. 3 вопроса за день
def daily_3_questions(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    today_str = datetime.now().strftime("%d.%m.%Y")
    today = datetime.now().date()

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_daily_3")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    if row[field_index] == today_str:
        return False

    today_count = 0
    for qa in qa_log[1:]:
        if qa[0] == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                if ts.date() == today:
                    today_count += 1
            except:
                continue

    if today_count >= 3:
        apply_mission_reward(row, xp_index, status_index, 2)
        row[field_index] = today_str
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

        return True

    return False

# ✅ 2. 3 дисциплины за день
def three_disciplines(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    today_str = datetime.now().strftime("%d.%m.%Y")
    today = datetime.now().date()

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_multi_disc")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    if row[field_index] == today_str:
        return False

    disciplines = set()
    for qa in qa_log[1:]:
        if qa[0] == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                if ts.date() == today:
                    disciplines.add(qa[4].strip().lower())
            except:
                continue

    if len(disciplines) >= 3:
        apply_mission_reward(row, xp_index, status_index, 5)
        row[field_index] = today_str
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

        return True

    return False

# ✅ 3. 10 вопросов за неделю
def weekly_10_questions(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    week_str = start_week.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_weekly_10")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    if row[field_index] == week_str:
        return False

    count = 0
    for qa in qa_log[1:]:
        if qa[0] == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                if ts.date() >= start_week:
                    count += 1
            except:
                continue

    if count >= 10:
        apply_mission_reward(row, xp_index, status_index, 10)
        row[field_index] = week_str
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

        return True

    return False

# ✅ 4. 50 XP за неделю
def weekly_50_xp(user_id):
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    week_str = start_week.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_weekly_50xp")
    xp_start_index = get_index("xp_start_of_week")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    if row[field_index] == week_str:
        return False

    current_xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
    start_xp = int(row[xp_start_index]) if row[xp_start_index].isdigit() else 0

    if (current_xp - start_xp) >= 50:
        apply_mission_reward(row, xp_index, status_index, 10)
        row[field_index] = week_str
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

        return True

    return False

# ✅ 5. 5 дисциплин за неделю
def weekly_5_disciplines(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    week_str = start_week.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_weekly_5disc")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    if row[field_index] == week_str:
        return False

    disciplines = set()
    for qa in qa_log[1:]:
        if qa[0] == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                if ts.date() >= start_week:
                    disciplines.add(qa[4].strip().lower())
            except:
                continue

    if len(disciplines) >= 5:
        apply_mission_reward(row, xp_index, status_index, 10)
        row[field_index] = week_str
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

        return True

    return False

# ✅ 6. 3 дня подряд с вопросами (стрик)
def streak_3_days(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    today = datetime.now().date()
    today_str = today.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_streak3")

    i, row = get_user_row(user_id)
    if not row:
        return False

    assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

    if row[field_index] == today_str:
        return False

    days_with_questions = set()
    for qa in qa_log[1:]:
        if qa[0] == str(user_id):
            try:
                ts = datetime.strptime(qa[1], "%d %B %Y, %H:%M")
                days_with_questions.add(ts.date())
            except:
                continue

    streak = all(
        (today - timedelta(days=offset)) in days_with_questions
        for offset in range(3)
    )

    if streak:
        apply_mission_reward(row, xp_index, status_index, 7)
        row[field_index] = today_str
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)

        return True

    return False

MISSIONS = [
    Mission("daily_3", "🎓 3 вопроса за день", "daily", 2, daily_3_questions),
    Mission("multi_disc", "📚 3 дисциплины за день", "daily", 5, three_disciplines),
    Mission("weekly_10", "💬 10 вопросов за неделю", "weekly", 10, weekly_10_questions),
    Mission("weekly_50xp", "🧠 50 XP за неделю", "weekly", 10, weekly_50_xp),
    Mission("weekly_5disc", "📙 5 дисциплин за неделю", "weekly", 10, weekly_5_disciplines),
    Mission("streak3", "✨ 3 дня подряд с вопросами", "weekly", 7, streak_3_days),
]

def get_all_missions():
    return MISSIONS

def apply_mission_reward(row, xp_index, status_index, reward):
    xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
    new_xp = xp + reward
    new_status, _, _ = determine_status(new_xp)

    row[xp_index] = str(new_xp)
    row[status_index] = new_status
