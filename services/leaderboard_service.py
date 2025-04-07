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

async def get_user_position_info(user_id: int) -> str:
    service = get_sheets_service()

    # Загружаем данные из таблицы
    sheet = service.spreadsheets().values()
    result = sheet.get(
        spreadsheetId=USER_SHEET_ID,
        range=f"{USER_SHEET_NAME}"
    ).execute()

    values = result.get("values", [])
    if not values or len(values) < 2:
        return "Не удалось загрузить данные пользователей."

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}

    xp_col = header_map.get("xp")
    id_col = header_map.get("user_id")
    name_col = header_map.get("first_name")
    status_col = header_map.get("status")

    if None in (xp_col, id_col, name_col, status_col):
        return "Не удалось найти нужные колонки в таблице."

    leaderboard = []
    for row in values[1:]:
        try:
            uid = int(row[id_col])
            xp = int(row[xp_col]) if xp_col < len(row) else 0
            name = row[name_col] if name_col < len(row) else "Без имени"
            status = row[status_col] if status_col < len(row) else "Неизвестно"
            leaderboard.append((uid, name, status, xp))
        except (ValueError, IndexError):
            continue

    leaderboard.sort(key=lambda x: x[3], reverse=True)

    for idx, (uid, name, status, xp) in enumerate(leaderboard, start=1):
        if uid == user_id:
            remaining = 0
            if xp <= 10:
                remaining = 11 - xp
                return f"👤 Ты сейчас на {idx} месте\n📈 До уровня «Опытный» осталось {remaining} XP"
            return f"👤 Ты сейчас на {idx} месте\n🎉 Ты достиг максимального уровня!"
    return "Ты ещё не в списке — задай свой первый вопрос!"
