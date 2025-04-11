from services.google_sheets_service import (
    update_user_plan, 
    get_all_users, 
    get_sheets_service,
    get_column_value_by_name,
)
from datetime import datetime, timedelta
from config import USER_SHEET_ID, USER_SHEET_NAME
import pytz
from services.sheets import update_sheet_row, get_user_row_by_id
from services.nft_service import generate_nft_card_if_needed
from aiogram import Bot


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
        "premium_status": "none"  # Начальная подписка "none"
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

def get_status_by_xp(xp: int) -> str:
    if xp >= 5000:
        return "👑 Создатель"
    elif xp >= 1000:
        return "🔥 Легенда"
    elif xp >= 300:
        return "🧠 Наставник"
    elif xp >= 150:
        return "👑 Эксперт"
    elif xp >= 50:
        return "🚀 Профи"
    elif xp >= 10:
        return "🔸 Опытный"
    else:
        return "🟢 Новичок"

def get_next_status(xp: int) -> tuple[str, int]:
    levels = [
        (5000, "👑 Создатель"),
        (1000, "🔥 Легенда"),
        (300, "🧠 Наставник"),
        (150, "👑 Эксперт"),
        (50, "🚀 Профи"),
        (10, "🔸 Опытный"),
        (0, "🟢 Новичок"),
    ]

    for threshold, status in levels:
        if xp < threshold:
            return status, threshold - xp

    return levels[0][1], 0  # если уже максимальный статус
   

async def activate_subscription(user_id: int, duration_days: int, internal_id: str):
    # "lite" или "pro" читаем из логов по internal_id (добавим позже или передадим как аргумент)
    plan_type = "lite" if "lite" in internal_id else "pro"

    await update_user_plan(user_id, plan_type, int(duration_days))

async def get_user_profile_text(user) -> str:
    row = await get_user_row_by_id(user.id)
    if not row:
        return "Профиль не найден."

    first_name = row.get("first_name") or user.first_name
    xp = int(row.get("xp", 0))
    actual_status = row.get("status") or get_status_by_xp(xp)  # используем статус из таблицы
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

    # NFT-карточка
    status_clean = actual_status.split()[-1]
    nft_url = row.get(f"nft_url_{status_clean}")
    nft_text = f"\n🎼 NFT-карточка: [Скачать]({nft_url})" if nft_url and status_clean in ["Наставник", "Легенда", "Создатель"] else ""

    # Прогресс-бар из 5 кубиков
    filled_blocks = min(xp * 5 // max(to_next + xp, 1), 5)
    progress_bar = f"{'🟩' * filled_blocks}{'⬜️' * (5 - filled_blocks)}"
    progress_percent = round((xp / (xp + to_next)) * 100) if to_next else 100

    return (
        f"👤 Имя: {first_name}\n"
        f"🎖️ Статус: {actual_status} — {progress_bar} {progress_percent}%\n"
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
        f"{plan_text}{nft_text}\n\n"
        f"👉 Подписку можно купить в разделе «🛒 Магазин»"
    )

async def increase_question_count(user_id: int):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    # Текущее время
    now = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")

    # Обновляем счётчики
    question_count = int(row.get("question_count", 0)) + 1
    day_count = int(row.get("day_count", 0)) + 1
    xp_week = int(row.get("xp_week", 0)) + 1
    streak_days = int(row.get("streak_days") or 0) + 1


    updates = {
        "question_count": question_count,
        "day_count": day_count,
        "xp_week": xp_week,
        "streak_days": streak_days,
        "last_interaction": now
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

async def decrease_question_limit(user_id: int):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    free = int(row.get("free_questions", 0))
    paid = int(row.get("paid_questions", 0))

    if free <= 0 and paid <= 0:
        return  # Нечего списывать

    if free > 0:
        free -= 1
    else:
        paid -= 1

    updates = {
        "free_questions": free,
        "paid_questions": paid,
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)



async def add_xp_and_update_status(user_id: int, delta: int = 1, bot: Bot = None):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    plan = row.get("premium_status", "").lower()
    if plan in ("lite", "pro"):
        return  # XP не начисляется, если активна подписка

    current_xp = int(row.get("xp", 0))
    new_xp = current_xp + delta

    old_status = row.get("status", "")
    new_status = get_status_by_xp(new_xp)

    now = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")

    updates = {
        "xp": new_xp,
        "status": new_status,
        "last_interaction": now
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

    # 💥 Если статус изменился — генерируем NFT и отправляем поздравление
    if new_status != old_status and bot:
        status_clean = new_status.split()[-1]
        nft_link = None

        if status_clean in ["Наставник", "Легенда", "Создатель"]:
            nft_link = await generate_nft_card_if_needed(user_id)

        messages = {
            "Опытный": (
                "🔸 Отлично! Теперь ты — <b>Опытный</b>!\n"
                "📗 Уверенные шаги к вершинам знаний. Продолжай!"
            ),
            "Профи": (
                "🚀 Ты теперь <b>Профи</b>!\n"
                "🔓 Твой путь только начинается — впереди ещё больше крутых достижений!"
            ),
            "Эксперт": (
                "👑 Вау! Ты стал <b>Экспертом</b>!\n"
                "📘 Уровень глубоких знаний — так держать!"
            ),
            "Наставник": (
                "🎉 Поздравляем! Ты стал 🧠 <b>Наставником</b>!\n"
                "📚 У тебя огромный опыт — делись знаниями, помогай другим!\n"
                f"🎼 <b>Твоя NFT-карточка достижений:</b>\n<a href=\"{nft_link}\">Скачать NFT</a>"
            ),
            "Легенда": (
                "🔥 Ты — <b>ЛЕГЕНДА</b>!\n"
                "🥇 Это путь упорства, знаний и роста.\n"
                f"🎼 <b>NFT-карточка:</b>\n<a href=\"{nft_link}\">Скачать NFT</a>"
            ),
            "Создатель": (
                "👑 Преклоняемся, <b>Создатель</b>!\n"
                "💫 Ты прошёл весь путь и стал абсолютом.\n"
                f"🎼 <b>Вот твоя NFT:</b>\n<a href=\"{nft_link}\">Скачать NFT</a>"
            )
        }

        status_key = status_clean
        if status_key in messages:
            await bot.send_message(
                chat_id=user_id,
                text=messages[status_key],
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            
               
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
    await update_sheet_row(sheet_id, "Users", user_id, {
        mission_name: "В процессе"
    })
  
async def update_user_subscription(user_id: int, plan: str):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    updates = {
        "premium_status": plan
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)
    
async def add_paid_questions(user_id: int, quantity: int):
    row = await get_user_row_by_id(user_id)
    if row:
        current_paid_questions = int(await get_column_value_by_name(
            row.sheet_id, "Users", row.index, "paid_questions"
        ))

        updated_paid_questions = current_paid_questions + quantity

        await update_sheet_row(row.sheet_id, row.sheet_name, row.index, {
            "paid_questions": updated_paid_questions
        })
        
async def update_user_after_answer(user_id: int, bot: Bot):
    await increase_question_count(user_id)
    await decrease_question_limit(user_id)
    await add_xp_and_update_status(user_id, bot=bot)

