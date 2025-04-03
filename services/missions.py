from datetime import datetime, timedelta
from services.google_sheets_service import (
    get_sheet_data, update_sheet_row, pad_user_row, USER_FIELDS, USER_SHEET_ID, PROGRAM_SHEETS
)
from services.user_service import determine_status

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

# 🎁 Награды за активность (стрик + XP)
def update_activity_rewards(user_id):
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today = datetime.now().date()
    today_str = today.strftime("%d.%m.%Y")

    streak_index = get_index("streak_days")
    last_streak_index = get_index("last_streak_date")
    xp_index = get_index("xp")
    free_index = get_index("free_questions")
    bonus_index = get_index("last_xp_bonus")

    for i, row in enumerate(values, start=2):
        if str(row[0]) != str(user_id):
            continue

        row = pad_user_row(row)
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

        update_sheet_row(USER_SHEET_ID, "Users", i, row)
        return

# ✅ 1. 3 вопроса за день
def daily_3_questions(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today_str = datetime.now().strftime("%d.%m.%Y")
    today = datetime.now().date()

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_daily_3")

    for i, row in enumerate(values, start=2):
        if row[0] != str(user_id):
            continue

        row = pad_user_row(row)
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
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 2
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[field_index] = today_str

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return True

    return False

# ✅ 2. 3 дисциплины за день
def three_disciplines(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today_str = datetime.now().strftime("%d.%m.%Y")
    today = datetime.now().date()

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_multi_disc")

    for i, row in enumerate(values, start=2):
        if row[0] != str(user_id):
            continue

        row = pad_user_row(row)
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
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 5
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[field_index] = today_str

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return True

    return False

# ✅ 3. 10 вопросов за неделю
def weekly_10_questions(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_weekly_10")

    for i, row in enumerate(values, start=2):
        if row[0] != str(user_id):
            continue

        row = pad_user_row(row)
        assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

        if row[field_index] == start_week.strftime("%d.%m.%Y"):
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
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 10
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[field_index] = start_week.strftime("%d.%m.%Y")

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return True

    return False

# ✅ 4. 50 XP за неделю
def weekly_50_xp(user_id):
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    today_str = start_week.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_weekly_50xp")
    xp_start_index = get_index("xp_start_of_week")

    for i, row in enumerate(values, start=2):
        if row[0] != str(user_id):
            continue

        row = pad_user_row(row)
        assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

        if row[field_index] == today_str:
            return False

        current_xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
        start_xp = int(row[xp_start_index]) if row[xp_start_index].isdigit() else 0

        if (current_xp - start_xp) >= 50:
            new_xp = current_xp + 10
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[field_index] = today_str

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return True

    return False

# ✅ 5. 5 дисциплин за неделю
def weekly_5_disciplines(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today = datetime.now().date()
    start_week = today - timedelta(days=today.weekday())
    today_str = start_week.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_weekly_5disc")

    for i, row in enumerate(values, start=2):
        if row[0] != str(user_id):
            continue

        row = pad_user_row(row)
        assert str(row[0]) == str(user_id), f"❗ Нарушение соответствия user_id при обновлении строки: ожидалось {user_id}, найдено {row[0]}"

        if row[field_index] == today_str:
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
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 10
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[field_index] = today_str

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
            return True

    return False

# ✅ 6. 3 дня подряд с вопросами (стрик)
def streak_3_days(user_id):
    qa_log = get_sheet_data(PROGRAM_SHEETS, "QA_Log")
    values = get_sheet_data(USER_SHEET_ID, "Users")
    today = datetime.now().date()
    today_str = today.strftime("%d.%m.%Y")

    xp_index = get_index("xp")
    status_index = get_index("status")
    field_index = get_index("last_streak3")

    for i, row in enumerate(values, start=2):
        if row[0] != str(user_id):
            continue

        row = pad_user_row(row)
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

        streak = True
        for offset in range(3):
            day = today - timedelta(days=offset)
            if day not in days_with_questions:
                streak = False
                break

        if streak:
            xp = int(row[xp_index]) if row[xp_index].isdigit() else 0
            new_xp = xp + 7
            new_status, _, _ = determine_status(new_xp)

            row[xp_index] = str(new_xp)
            row[status_index] = new_status
            row[field_index] = today_str

            update_sheet_row(USER_SHEET_ID, "Users", i, row)
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