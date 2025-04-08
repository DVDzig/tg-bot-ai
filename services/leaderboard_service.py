import logging
from config import USER_SHEET_ID, USER_SHEET_NAME
from services.sheets import get_sheets_service
from utils.xp_logic import get_status_by_xp
from services.google_sheets_service import get_all_users

logger = logging.getLogger(__name__)


async def get_leaderboard_text(current_user_id: int) -> str:
    service = get_sheets_service()
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=USER_SHEET_ID,
            range=f"{USER_SHEET_NAME}!A1:Z1000"
        ).execute()
    except Exception as e:
        logger.exception("Ошибка при получении данных для лидерборда:")
        return "⚠️ Не удалось загрузить таблицу с пользователями."

    values = result.get("values", [])
    leaderboard = []

    for row in values[1:]:
        try:
            user_id = int(row[0]) if len(row) > 0 else 0
            name = row[2] if len(row) > 2 else "—"
            xp = int(row[17]) if len(row) > 17 else 0
            leaderboard.append((user_id, name, xp))
        except Exception as e:
            logger.warning(f"Ошибка при обработке строки: {row} — {e}")
            continue

    leaderboard.sort(key=lambda x: x[2], reverse=True)
    top_10 = leaderboard[:10]

    logger.info(f"Лидерборд сформирован. Всего пользователей: {len(leaderboard)}")

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
                logger.info(f"Пользователь {uid} находится на {idx} месте")
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
        except Exception as e:
            logger.warning(f"Ошибка при обработке пользователя: {u} — {e}")
            continue

    top_users.sort(reverse=True)
    logger.info("Кэш лидерборда обновлён.")


async def get_user_position_info(user_id: int) -> str:
    service = get_sheets_service()
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=USER_SHEET_ID,
            range=f"{USER_SHEET_NAME}"
        ).execute()
    except Exception as e:
        logger.exception("Ошибка при загрузке данных пользователей:")
        return "Не удалось загрузить данные пользователей."

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
        logger.error("Не найдены все нужные колонки в таблице.")
        return "Не удалось найти нужные колонки в таблице."

    leaderboard = []
    for row in values[1:]:
        try:
            uid = int(row[id_col])
            xp = int(row[xp_col]) if xp_col < len(row) else 0
            name = row[name_col] if name_col < len(row) else "Без имени"
            status = row[status_col] if status_col < len(row) else "Неизвестно"
            leaderboard.append((uid, name, status, xp))
        except Exception as e:
            logger.warning(f"Ошибка при обработке строки лидерборда: {row} — {e}")
            continue

    leaderboard.sort(key=lambda x: x[3], reverse=True)

    for idx, (uid, name, status, xp) in enumerate(leaderboard, start=1):
        if uid == user_id:
            logger.info(f"Пользователь {user_id} найден в лидерборде на позиции {idx}")
            if xp <= 10:
                remaining = 11 - xp
                return f"👤 Ты сейчас на {idx} месте\n📈 До уровня «Опытный» осталось {remaining} XP"
            return f"👤 Ты сейчас на {idx} месте\n🎉 Ты достиг максимального уровня!"

    logger.info(f"Пользователь {user_id} не найден в таблице.")
    return "Ты ещё не в списке — задай свой первый вопрос!"
