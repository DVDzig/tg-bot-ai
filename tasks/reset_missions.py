from datetime import datetime, timedelta
from services.google_sheets_service import (
    get_all_users,
    update_sheet_row
)

async def reset_daily_missions():
    users = await get_all_users()

    for row in users:
        updates = {}

        # Обнуление флагов миссий
        updates["daily_mission_done"] = ""
        updates["streak_mission_done"] = ""

        # Если сегодня понедельник — обнуляем и weekly
        if datetime.utcnow().weekday() == 0:
            updates["weekly_mission_done"] = ""

        # Обновляем streak_days
        day_count = int(row.get("day_count", 0))
        prev_streak = int(row.get("streak_days", 0))
        if day_count > 0:
            updates["streak_days"] = str(prev_streak + 1)
        else:
            updates["streak_days"] = "0"

        # Обнуляем day_count на следующий день
        updates["day_count"] = "0"

        await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

async def reset_expired_subscriptions():
    users = await get_all_users()
    today = datetime.utcnow().date()

    for user in users:
        user_id = user.get("user_id")
        premium_until = user.get("premium_until", "").strip()

        if not premium_until or premium_until.lower() == "none":
            continue

        try:
            until_date = datetime.strptime(premium_until, "%Y-%m-%d").date()
        except ValueError:
            continue

        if until_date < today:
            updates = {
                "plan": "",
                "premium_status": "",
                "premium_until": "",
                "next_plan": "",
                "next_until": ""
            }
            await update_sheet_row(user.sheet_id, user.sheet_name, user.index, updates)
