from google_sheets_service import (
    update_user_xp,
    get_user_row_by_id,
    update_sheet_row,
    get_column_index
)
from datetime import datetime

async def check_and_apply_missions(user_id: int) -> list[str]:
    # Получаем данные о пользователе из таблицы
    row = await get_user_row_by_id(user_id)
    if not row:
        return []

    messages = {}
    updates = {}

    # Получаем индексы граф для миссий
    daily_mission_column = await get_column_index(row.sheet_id, row.sheet_name, "Ежедневная миссия")
    weekly_mission_column = await get_column_index(row.sheet_id, row.sheet_name, "Недельная миссия")
    streak_mission_column = await get_column_index(row.sheet_id, row.sheet_name, "Стрик-миссия")

    # Проверяем ежедневную миссию (задано 3 вопроса)
    day_count = int(row.get("day_count", 0))
    daily_done = row.get(f"daily_mission_done", "")
    if day_count >= 3 and daily_done != "1":
        await update_user_xp(user_id, 5)
        updates[f"daily_mission_done"] = "1"
        messages["daily"] = "🎯 Ежедневная миссия выполнена! +5 XP"

    # Проверяем недельную миссию (10 XP за неделю)
    xp_week = int(row.get("xp_week", 0))
    weekly_done = row.get(f"weekly_mission_done", "")
    if xp_week >= 10 and weekly_done != "1":
        await update_user_xp(user_id, 10)
        updates[f"weekly_mission_done"] = "1"
        messages["weekly"] = "📅 Недельная миссия выполнена! +10 XP"

    # Проверяем стрик-миссию (3 дня подряд)
    streak = int(row.get("streak_days", 0))
    streak_done = row.get(f"streak_mission_done", "")
    if streak >= 3 and streak_done != "1":
        await update_user_xp(user_id, 15)
        updates[f"streak_mission_done"] = "1"
        messages["streak"] = "🔥 Стрик! 3 дня активности подряд — +15 XP"

    # Обновляем таблицу с новыми статусами миссий
    if updates:
        await update_sheet_row(
            sheet_id=row.sheet_id,
            sheet_name=row.sheet_name,
            row_index=row.index,
            updates=updates
        )

    return list(messages.values())

async def get_user_missions_text(user_id: int) -> str:
    row = await get_user_row_by_id(user_id)
    if not row:
        return "Не удалось получить данные пользователя."

    day_count = int(row.get("day_count", 0))
    xp_week = int(row.get("xp_week", 0))
    streak_days = int(row.get("streak_days", 0))

    missions = []

    # Ежедневная
    if day_count >= 3:
        missions.append("✅ Задать 3 вопроса за день — +5 XP")
    else:
        missions.append(f"⏳ Задать 3 вопроса за день ({day_count}/3) — +5 XP")

    # Недельная
    if xp_week >= 10:
        missions.append("✅ Получить 10 XP за неделю — +10 XP")
    else:
        missions.append(f"⏳ Получить 10 XP за неделю ({xp_week}/10) — +10 XP")

    # Стрик
    if streak_days >= 3:
        missions.append("✅ 3 дня подряд активности — +15 XP")
    else:
        missions.append(f"⏳ 3 дня подряд активности ({streak_days}/3) — +15 XP")

    text = "🎯 <b>Твои миссии</b>\n\n" + "\n".join(missions)
    text += "\n\n🔥 Выполняй миссии и зарабатывай XP для повышения статуса!"
    return text
