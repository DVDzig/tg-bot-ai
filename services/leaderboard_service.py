from config import USER_SHEET_ID, USER_SHEET_NAME
from services.sheets import get_sheets_service
from utils.xp_logic import get_status_by_xp, get_next_status_info
from services.google_sheets_service import get_all_users


async def get_leaderboard_text(current_user_id: int) -> str:
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=USER_SHEET_ID,
        range=f"{USER_SHEET_NAME}!A1:R" # A: user_id, C: first_name, R: xp
    ).execute()

    values = result.get("values", [])
    leaderboard = []

    for row in values[1:]:
        try:
            user_id = int(row[0]) if len(row) > 0 else 0
            name = row[2] if len(row) > 2 else "—"
            xp = int(row[17]) if len(row) > 17 else 0
            leaderboard.append((user_id, name, xp))
        except:
            continue

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

from services.sheets import get_column_index_by_name

async def get_leaderboard_text(current_user_id: int) -> str:
    service = get_sheets_service()
    
    # Получаем названия нужных колонок
    col_user_id = await get_column_index_by_name(USER_SHEET_ID, USER_SHEET_NAME, "user_id")
    col_first_name = await get_column_index_by_name(USER_SHEET_ID, USER_SHEET_NAME, "first_name")
    col_xp = await get_column_index_by_name(USER_SHEET_ID, USER_SHEET_NAME, "xp")

    if None in (col_user_id, col_first_name, col_xp):
        return "⚠️ Не удалось получить данные для лидерборда."

    # Определяем буквенные названия колонок
    def col_letter(index): return chr(ord("A") + index)
    range_str = f"{USER_SHEET_NAME}!{col_letter(col_user_id)}:{col_letter(col_xp)}"

    result = service.spreadsheets().values().get(
        spreadsheetId=USER_SHEET_ID,
        range=range_str
    ).execute()

    values = result.get("values", [])
    leaderboard = []

    for row in values[1:]:
        try:
            user_id = int(row[0]) if len(row) > 0 else 0
            name = row[1] if len(row) > 1 else "—"
            xp = int(row[2]) if len(row) > 2 else 0
            leaderboard.append((user_id, name, xp))
        except:
            continue

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

    if current_user_id not in [u[0] for u in top_10]:
        for idx, (uid, name, xp) in enumerate(leaderboard, start=1):
            if uid == current_user_id:
                status = get_status_by_xp(xp)
                text += f"\n👤 Ты сейчас на {idx} месте\n"
                text += f"📈 Твой статус: {status}, {xp} XP\n"
                break

    return text
