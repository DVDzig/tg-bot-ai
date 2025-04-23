from datetime import datetime, timedelta
from services.google_sheets_service import (
    get_all_users,
    update_sheet_row
)
import random


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
            from services.sheets import get_user_row_by_id
            row = await get_user_row_by_id(user_id)

            if row:
                updates = {
                    "plan": "",
                    "premium_status": "",
                    "premium_until": "",
                    "next_plan": "",
                    "next_until": ""
                }
                await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)
                print(f"[EXPIRED] Подписка у пользователя {user_id} сброшена")

async def send_reminder_messages():
    from bot import bot
    users = await get_all_users()
    now = datetime.now()
    today = now.date()

    for user in users:
        user_id = user.get("user_id")
        last_reminder_str = user.get("last_reminder_date", "")
        status = user.get("status", "Новичок")
        xp = int(user.get("xp", 0))
        free_q = int(user.get("free_questions", 0))
        paid_q = int(user.get("paid_questions", 0))


        try:
            last_reminder = datetime.strptime(last_reminder_str, "%Y-%m-%d").date()
        except:
            last_reminder = None

        # Рандомный шаг (5–7 дней)
        days_since = (today - last_reminder).days if last_reminder else 999
        if days_since < 5:
            continue  # ещё не пора

        # Рандомное окно: 10–13 или 16–19
        hour = random.choice(range(10, 14)) if random.random() < 0.5 else random.choice(range(16, 20))
        minute = random.randint(0, 59)

        # Фильтрация по текущему часу
        if now.hour != hour:
            continue

        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=(
                    "👋 Давненько не виделись!\n\n"
                    "У тебя всё ещё активны миссии, а ещё:\n"
                    f"• Осталось <b>{free_q}</b> бесплатных и <b>{paid_q}</b> платных вопросов\n"
                    f"• Статус: <b>{status}</b>\n"
                    f"• XP: <b>{xp}</b>\n\n"
                    "Загляни и проверь, что нового 👀"
                ),
                parse_mode="HTML"
            )

            await update_sheet_row(user.sheet_id, user.sheet_name, user.index, {
                "last_reminder_date": today.strftime("%Y-%m-%d")
            })

            print(f"[REMINDER] Отправлено пользователю {user_id}")

        except Exception as e:
            print(f"[REMINDER ERROR] {user_id}: {e}")
