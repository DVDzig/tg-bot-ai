from config import USER_SHEET_ID, USER_SHEET_NAME
from utils.sheets import get_sheets_service
from utils.xp_logic import get_status_by_xp, get_next_status_info
from google_sheets_service import get_all_users


async def get_leaderboard_text(current_user_id: int) -> str:
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=USER_SHEET_ID,
        range=f"{USER_SHEET_NAME}!A,C,R"  # A: user_id, C: first_name, R: xp
    ).execute()

    values = result.get("values", [])
    leaderboard = []

    for row in values[1:]:  # пропустить заголовок
        if len(row) >= 3:
            user_id = int(row[0])
            name = row[1]
            xp = int(row[2])
            leaderboard.append((user_id, name, xp))

    leaderboard.sort(key=lambda x: x[2], reverse=True)

    top_10 = leaderboard[:10]
    text = "🏆 <b>Топ-10 пользователей по XP:</b>\n\n"

    for idx, (uid, name, xp) in enumerate(top_10, start=1):
        you = " (ты)" if uid == current_user_id else ""
        status = get_status_by_xp(xp)
        text += f"🥇 {name} — {status}, {xp} XP{you}\n" if idx == 1 else \
                f"🥈 {name} — {status}, {xp} XP{you}\n" if idx == 2 else \
                f"🥉 {name} — {status}, {xp} XP{you}\n" if idx == 3 else \
                f"{idx}. {name} — {status}, {xp} XP{you}\n"

    # Показать место пользователя вне топа
    if current_user_id not in [u[0] for u in top_10]:
        for idx, (uid, name, xp) in enumerate(leaderboard, start=1):
            if uid == current_user_id:
                status = get_status_by_xp(xp)
                text += f"\n👤 Ты сейчас на {idx} месте\n"
                text += f"📈 Твой статус: {status}, {xp} XP\n"
                break

    return text

async def update_leaderboard_cache():
    users = await get_all_users()
    top_users = []

    for u in users:
        try:
            xp = int(u.get("xp", 0))
            name = u.get("first_name", "—")
            status = get_status_by_xp(xp)
            top_users.append((xp, name, status))
        except:
            continue

    # Сортируем по XP
    top_users.sort(reverse=True)

    # Опционально: сохранить в global переменную / redis / файл
    with open("leaderboard.txt", "w", encoding="utf-8") as f:
        for idx, (xp, name, status) in enumerate(top_users[:10], start=1):
            f.write(f"{idx}. {name} — {status}, {xp} XP\n")

async def get_user_position_info(user_id: int) -> str:
    users = await get_all_users()

    # Собираем (user_id, xp) и сортируем
    ranked = []
    for u in users:
        try:
            xp = int(u.get("xp", 0))
            uid = int(u.get("user_id"))
            ranked.append((uid, xp))
        except:
            continue

    ranked.sort(key=lambda x: x[1], reverse=True)

    # Позиция пользователя
    position = next((idx + 1 for idx, (uid, _) in enumerate(ranked) if uid == user_id), None)

    # Информация о себе
    user_xp = next((xp for uid, xp in ranked if uid == user_id), 0)
    user_status = get_status_by_xp(user_xp)
    next_status, to_next = get_next_status_info(user_xp)

    if position is None:
        return "Ты пока не в рейтинге."

    msg = f"👤 Ты сейчас на <b>{position}</b> месте\n"
    if next_status:
        msg += f"📈 До уровня «{next_status}» осталось <b>{to_next} XP</b>"
    else:
        msg += f"🎉 Ты достиг максимального уровня!"

    return msg
