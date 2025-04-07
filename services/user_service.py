from utils.xp_logic import get_status_by_xp, get_next_status
from services.google_sheets_service import (
    get_user_row_by_id, 
    update_user_plan, 
    get_all_users,
    get_column_index, 
    get_sheets_service,
    get_column_value_by_name,
    update_sheet_row  # Импорт функции чтения из таблицы
)
from datetime import datetime, timedelta
from config import USER_SHEET_ID, USER_SHEET_NAME

async def get_or_create_user(user) -> None:
    """
    Проверяет, существует ли пользователь в таблице. Если нет — создаёт нового.
    """
    # Проверяем, есть ли пользователь в таблице
    row = await get_user_row_by_id(user.id)
    
    if row:
        return  # Если пользователь уже есть, ничего не делаем

    # Если пользователя нет, создаем новую строку с данными пользователя
    new_user_data = {
        "user_id": user.id,
        "username": user.username or "",  # Подставляем пустую строку, если нет username
        "first_name": user.first_name,
        "last_name": user.last_name or "",  # Если last_name пустое, ставим пустую строку
        "language_code": user.language_code or "en",  # Язык по умолчанию - "en"
        "is_premium": str(getattr(user, "is_premium", False)).lower(),
        "first_interaction": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "last_interaction": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "question_count": 0,
        "day_count": 0,
        "status": "Новичок",
        "xp": 0,
        "xp_week": 0,
        "paid_questions": 0,
        "last_free_reset": "2025-01-01 00:00:00",
        "free_questions": 10,  # Начальное количество бесплатных вопросов
        "streak_days": 0,
        "daily_mission_done": "0",
        "weekly_mission_done": "0",
        "streak_mission_done": "0",
        "subscription_plan": "none"  # Начальная подписка "none"
    }

    # Добавляем нового пользователя в таблицу
    service = get_sheets_service()
    range_ = f"{USER_SHEET_NAME}!A2:Z"  # Начинаем с 2-й строки (первая — это заголовок)
    
    # Записываем данные пользователя в таблицу
    body = {
        "values": [list(new_user_data.values())]
    }
    service.spreadsheets().values().append(
        spreadsheetId=USER_SHEET_ID,
        range=range_,
        valueInputOption="RAW",
        body=body
    ).execute()

async def activate_subscription(user_id: int, duration_days: int, internal_id: str):
    # "lite" или "pro" читаем из логов по internal_id (добавим позже или передадим как аргумент)
    plan_type = "lite" if "lite" in internal_id else "pro"

    until_date = (datetime.utcnow() + timedelta(days=duration_days)).strftime("%Y-%m-%d")
    await update_user_plan(user_id, plan_type, until_date)

async def get_user_profile_text(user) -> str:
    if user.id == 150532949:
        return (
            f"👤 Имя: {user.first_name}\n"
            f"👑 Статус: Создатель — 🟩🟩🟩🟩🟩 100%\n"
            f"⭐ Твой XP: 9999 XP\n"
            f"📅 Последний вход: —\n\n"
            f"🎁 Доступные вопросы:\n"
            f"• Бесплатные: 999\n"
            f"• Платные: 999\n\n"
            f"📈 Активность:\n"
            f"• Сегодня: ∞\n"
            f"• За неделю: ∞\n"
            f"• Всего: ∞\n\n"
            f"🔥 У тебя безлимит — ты Создатель.\n\n"
            f"🔓 Подписка: Полный доступ (админ)\n"
        )

    # Стандартный путь
    row = await get_user_row_by_id(user.id)
    if not row:
        return "Профиль не найден."

    first_name = row.get("first_name") or user.first_name
    xp = int(row.get("xp", 0))
    status = get_status_by_xp(xp)
    next_status, to_next = get_next_status(xp)

    free_q = int(row.get("free_questions", 0))
    paid_q = int(row.get("paid_questions", 0))

    last_login = row.get("last_interaction", "")
    last_login_str = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y, %H:%M") if last_login else "—"

    today_q = int(row.get("day_count", 0))
    week_q = int(row.get("xp_week", 0))
    total_q = int(row.get("question_count", 0))

    plan = row.get("plan", "")
    plan_text = ""
    if plan == "lite":
        plan_text = "🔓 Подписка: Лайт (безлимит)"
    elif plan == "pro":
        plan_text = "🔓 Подписка: Про (приоритет, 100 вопросов, видео)"

    # Прогресс-бар из 5 кубиков
    filled_blocks = min(xp * 5 // max(to_next + xp, 1), 5)
    progress_bar = f"{'🟩' * filled_blocks}{'⬜️' * (5 - filled_blocks)}"
    progress_percent = round((xp / (xp + to_next)) * 100) if to_next else 100

    return (
        f"👤 Имя: {first_name}\n"
        f"🎖️ Статус: {status} — {progress_bar} {progress_percent}%\n"
        f"⭐ Твой XP: {xp} XP\n"
        f"📅 Последний вход: {last_login_str}\n\n"

        f"🎁 Доступные вопросы:\n"
        f"• Бесплатные: {free_q}\n"
        f"• Платные: {paid_q}\n\n"

        f"📈 Активность:\n"
        f"• Сегодня: {today_q} вопрос(ов)\n"
        f"• За неделю: {week_q} вопрос(ов)\n"
        f"• Всего: {total_q} вопрос(ов)\n\n"

        f"🔥 Сегодня ты уже задал {today_q} из 3 вопросов!\n\n"
        f"💡 Ближайший статус: {next_status} (ещё {to_next} XP)\n\n"
        f"{plan_text}\n\n"
        f"👉 Подписку можно купить в разделе «🛒 Магазин»"
    )

async def increase_question_count(user_id: int):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    updates = {
        "question_count": str(int(row.get("question_count", 0)) + 1),
        "day_count": str(int(row.get("day_count", 0)) + 1),
        "week_count": str(int(row.get("week_count", 0)) + 1),
        "total_questions": str(int(row.get("total_questions", 0)) + 1),
        "last_interaction": datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)


async def decrease_question_limit(user_id: int):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    free = int(row.get("free_questions", 0))
    paid = int(row.get("paid_questions", 0))

    if free > 0:
        free -= 1
    elif paid > 0:
        paid -= 1

    updates = {
        "free_questions": str(free),
        "paid_questions": str(paid)
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

def get_status_by_xp(xp: int) -> str:
    if xp <= 10:
        return "Новичок"
    elif xp <= 50:
        return "Опытный"
    elif xp <= 100:
        return "Профи"
    elif xp <= 200:
        return "Эксперт"
    else:
        return "Наставник"

async def add_xp_and_update_status(user_id: int, delta: int = 1):
    row = await get_user_row_by_id(user_id)
    if not row or row.get("plan") in ("lite", "pro"):
        return

    xp = int(row.get("xp", 0))
    new_xp = xp + delta
    new_status = get_status_by_xp(new_xp)

    updates = {
        "xp": str(new_xp),
        "status": new_status
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

async def monthly_bonus_for_user(user_row):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    last_bonus = user_row.get("last_bonus_date")

    if last_bonus == today:
        return  # Уже выдано сегодня

    status = user_row.get("status", "Новичок")
    current = int(user_row.get("free_questions", 0))

    bonus_map = {
        "Новичок": 5,
        "Опытный": 10,
        "Профи": 20,
        "Эксперт": 30,
        "Наставник": 50,
        "Легенда": 75,
        "Создатель": 100
    }

    bonus = bonus_map.get(status, 0)
    updates = {
        "free_questions": str(current + bonus),
        "last_bonus_date": today
    }

    await update_sheet_row(user_row.sheet_id, user_row.sheet_name, user_row.index, updates)

async def apply_monthly_bonus_to_all_users():
    users = await get_all_users()
    for user in users:
        await monthly_bonus_for_user(user)
        
async def create_mission(sheet_id: str, mission_name: str, user_id: int):
    """
    Функция для добавления новой миссии в таблицу пользователя.
    :param sheet_id: ID таблицы
    :param mission_name: Название миссии
    :param user_id: ID пользователя
    """

    # Получаем индекс колонки для миссии
    mission_column = await get_column_index(sheet_id, "Users", mission_name)

    # Создаём или обновляем статус миссии для пользователя
    service = get_sheets_service()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"Users!{chr(65 + mission_column)}{user_id + 2}",  # Строки с 2 (первый пользователь)
        valueInputOption="RAW",
        body={"values": [["В процессе"]]}  # Статус миссии по умолчанию
    ).execute()
    
async def update_user_subscription(user_id: int, plan: str):
    row = await get_user_row_by_id(user_id)
    if row:
        # Получаем индекс колонки "subscription_plan"
        subscription_column = await get_column_index(row.sheet_id, "Users", "subscription_plan")
        
        # Обновляем статус подписки
        service = get_sheets_service()
        service.spreadsheets().values().update(
            spreadsheetId=row.sheet_id,
            range=f"Users!{chr(65 + subscription_column)}{row.index + 2}",
            valueInputOption="RAW",
            body={"values": [[plan]]}
        ).execute()

async def add_paid_questions(user_id: int, quantity: int):
    row = await get_user_row_by_id(user_id)
    if row:
        # Получаем индекс колонки "paid_questions"
        paid_questions_column = await get_column_index(row.sheet_id, "Users", "paid_questions")
        
        # Получаем текущее количество оплаченных вопросов
        current_paid_questions = int(await get_column_value_by_name(row.sheet_id, "Users", row.index, "paid_questions"))
        
        # Обновляем количество оплаченных вопросов
        updated_paid_questions = current_paid_questions + quantity

        service = get_sheets_service()
        service.spreadsheets().values().update(
            spreadsheetId=row.sheet_id,
            range=f"Users!{chr(65 + paid_questions_column)}{row.index + 2}",
            valueInputOption="RAW",
            body={"values": [[updated_paid_questions]]}
        ).execute()
