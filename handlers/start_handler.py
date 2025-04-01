from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.keyboard import get_main_keyboard
from services.user_service import (
    apply_xp_penalty_if_needed,
    get_user_activity_stats,
    determine_status,
    get_user_profile, 
    get_or_create_user
)
from services.google_sheets_service import get_leaderboard, get_sheet_data
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.markdown import hlink
from services.yookassa_service import create_payment
from config import USER_SHEET_ID


router = Router()

# Главное меню
@router.message(Command("start"))
async def start_handler(message: types.Message):
    user = message.from_user
    get_or_create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language_code=user.language_code,
        is_premium=getattr(user, "is_premium", False)
    )
    apply_xp_penalty_if_needed(user.id)

    welcome_text = (
        "Привет 👋\n\n"
        "Я — Образовательный консультант, помогу тебе разобраться в дисциплинах, подготовиться к экзаменам и выбрать нужную программу обучения.\n\n"
        "🧠 Отвечаю на вопросы строго по теме — если в вопросе нет ключевых слов, связанных с дисциплиной, я не смогу ответить.\n\n"
        "🎯 За каждый вопрос ты получаешь XP и растёшь в статусе:\n"
        "🟢 Новичок — 0–10 XP\n"
        "🔸 Опытный — 11–50 XP\n"
        "🚀 Профи — 51–100 XP\n"
        "👑 Эксперт — 101+ XP\n\n"
        "💰 Вопросы заканчиваются? Купи дополнительные — и продолжай обучение.\n"
        "📈 Следи за прогрессом и активностью в разделе «Мой профиль».\n"
        "🎥 А если ты Профи или Эксперт — я порекомендую тебе ещё и видео по теме.\n\n"
        "Готов? Выбирай действие ⤵️"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

async def go_to_start_screen(message: types.Message):
    text = (
        "📚 Главное меню готово к работе!\n\n"
        "❓ Задавай вопросы по дисциплине и получай XP\n"
        "🏆 Выполняй ежедневный челлендж (3 вопроса в день — и бонус XP)\n"
        "🎥 Профи и Эксперты получают видео по теме\n"
        "💰 Закончились вопросы? Купи пакет и продолжай учиться\n\n"
        "Выбери действие ниже ⤵️"
    )
    await message.answer(text, reply_markup=get_main_keyboard())

# Обработчик кнопки "Мой профиль"
@router.message(lambda message: message.text == "👤 Мой профиль")
async def profile_handler(message: types.Message):
    user_id = message.from_user.id
    profile_data = get_user_profile(user_id)
    stats = get_user_activity_stats(user_id)
    payment_log = get_sheet_data(USER_SHEET_ID, "PaymentsLog!A2:G")
    last_payment = None
    for row in reversed(payment_log):
        if row[0] == str(user_id) and row[4] == "payment.succeeded":
            last_payment = row
            break

    if last_payment:
        q_count = last_payment[2]
        price = last_payment[1]
        date = last_payment[6]
        last_purchase_text = f"\n🧾 <b>Последняя покупка:</b>\n• {q_count} вопрос(ов), {price}₽\n• {date}"
    else:
        last_purchase_text = ""

    current_xp = profile_data['xp']
    new_status, _ = determine_status(current_xp)

    thresholds = {
        "новичок": (0, 10),
        "опытный": (11, 50),
        "профи": (51, 100),
        "эксперт": (101, 150)
    }
    min_xp, max_xp = thresholds.get(new_status, (0, 10))
    if current_xp >= max_xp:
        progress = 100
    else:
        progress = int(((current_xp - min_xp) / (max_xp - min_xp)) * 100)
    bar_blocks = min(5, int(progress / 5))
    progress_bar = "🟩" * bar_blocks + "⬜️" * (5 - bar_blocks)

    daily_goal = 3
    challenge_text = (
        f"🔥 Сегодня ты уже задал {stats['today']} из {daily_goal} вопросов!"
        if stats['today'] < daily_goal
        else "🏆 Ты выполнил ежедневный челлендж!"
    )
    # Определим ближайший статус и сколько XP до него
    next_status_info = {
        "новичок": ("опытный", 11),
        "опытный": ("профи", 51),
        "профи": ("эксперт", 101),
        "эксперт": ("эксперт", 9999)
    }
    next_status, xp_target = next_status_info.get(new_status, ("опытный", 11))
    xp_left = max(0, xp_target - current_xp)

    profile_text = (
        f"👤 <b>Имя:</b> {profile_data['first_name']}\n"
        f"🎖️ <b>Статус:</b> {new_status.capitalize()} — {progress_bar} {progress}%\n"
        f"⭐ <b>Твой XP:</b> {current_xp} XP\n"
        f"📅 <b>Последний вход:</b> {profile_data['last_interaction']}\n\n"

        f"🎁 <b>Доступные вопросы:</b>\n"
        f"• Бесплатные: {profile_data['free_questions']}\n"
        f"• Платные: {profile_data['paid_questions']}\n"

        f"{last_purchase_text}\n\n"

        f"📈 <b>Активность:</b>\n"
        f"• Сегодня: {stats['today']} вопрос(ов)\n"
        f"• За неделю: {stats['week']} вопрос(ов)\n"
        f"• Всего: {stats['total']} вопрос(ов)\n\n"

        f"{challenge_text}\n\n"
        + (
            f"💡 <i>Ближайший статус:</i> {next_status} (ещё {xp_left} XP)\n"
            if new_status != "эксперт"
            else "🎓 Ты уже достиг максимального уровня! Поздравляем! 🏆\n"
        )
    )


    await message.answer(profile_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# Обработка кнопки "📊 Лидерборд"
@router.message(lambda msg: msg.text == "📊 Лидерборд")
async def leaderboard_handler(message: types.Message):
    leaderboard = get_leaderboard(top_n=100)  # Получим сразу 100, чтобы найти место пользователя
    if not leaderboard:
        await message.answer("🏆 Пока что нет пользователей в рейтинге.")
        return

    user_id = str(message.from_user.id)
    user_profile = get_user_profile(int(user_id))
    current_xp = user_profile['xp']
    user_place = None

    # Формируем текст топ-10
    top_text = "🏆 <b>Топ-10 пользователей по XP</b>:\n\n"
    for idx, entry in enumerate(leaderboard[:10], start=1):
        name = entry.get("first_name") or f"@{entry.get('username', 'неизвестно')}"
        status, _ = determine_status(entry['xp'])

        # Иконка статуса
        status_icon = {
            "новичок": "🟢",
            "опытный": "🔸",
            "профи": "🚀",
            "эксперт": "👑"
        }.get(status, "❓")

        # Иконка места
        place_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx}.")
        highlight = " (ты)" if entry['user_id'] == user_id else ""

        top_text += f"{place_emoji} {name} — {status_icon} {entry['xp']} XP{highlight}\n"

    # Найдём текущее место пользователя
    for idx, entry in enumerate(leaderboard, start=1):
        if entry['user_id'] == user_id:
            user_place = idx
            break

    # Определим следующую цель
    current_status, _ = determine_status(current_xp)
    next_status_info = {
        "новичок": ("опытный", 11),
        "опытный": ("профи", 51),
        "профи": ("эксперт", 101),
        "эксперт": ("эксперт", 9999)
    }
    next_status, xp_target = next_status_info.get(current_status, ("опытный", 11))
    xp_left = max(0, xp_target - current_xp)

    # Хвост сообщения
    tail = f"\n👤 Ты сейчас на {user_place} месте"
    if current_status == "эксперт":
        tail += "\n🎓 Ты достиг максимального уровня! Продолжай учиться и помогай другим 💪"
    else:
        tail += f"\n📈 До уровня «{next_status}» осталось {xp_left} XP\n"
        tail += "Продолжай в том же духе! 💪"

    await message.answer(top_text + tail, parse_mode="HTML")

# Обработка кнопки "❓ Помощь"
@router.message(lambda m: m.text and "помощь" in m.text.lower())
async def help_handler(message: types.Message):
    help_text = (
        "ℹ️ <b>О боте</b>\n"
        "Я — Образовательный консультант по учебным дисциплинам. Помогаю готовиться к экзаменам.\n\n"
        "❓ <b>Как это работает?</b>\n"
        "• Задаешь вопросы по выбранной дисциплине — получаешь ответ.\n"
        "• За каждый вопрос ты получаешь 1 XP (очки активности).\n"
        "• XP повышают твой статус и открывают бонусы.\n\n"
        "⚙️ Ответы формируются на основе ключевых слов по каждой дисциплине. Если в вопросе нет слов из темы — ответа не будет.\n\n"
        "🏆 <b>Статусы и XP</b>\n"
        "• 🟢 Новичок 0–10 XP\n"
        "• 🔸 Опытный 11–50 XP\n"
        "• 🚀 Профи 51–100 XP\n"
        "• 👑 Эксперт 101+ XP\n\n"
        "⚠️ Не заходил 5 дней — минус 5 XP\n"
        "⚠️ Не заходил 10 дней — минус 10 XP\n\n"
        "💳 <b>Закончились вопросы?</b>\n"
        "Покупай дополнительные вопросы прямо в боте.\n\n"
        "🎁 <b>Бонусы</b>\n"
        "Участвуй в розыгрышах среди активных пользователей!\n\n"
        "📝 <b>Памятка по вопросам</b>\n"
        "• Вопросы — строго по дисциплине, которую выбрал.\n"
        "• Не задавай общие/несвязанные вопросы — бот не ответит.\n"
        "• Чем конкретнее вопрос — тем лучше ответ.\n\n"
        "<i>Примеры:</i>\n"
        "✅ <i>«Что такое медиапланирование в спорте?»</i>\n"
        "❌ <i>«Расскажи что-нибудь»</i>\n\n"
        "📄 <b>Условия использования, политика и оплата:</b>\n"
        "<a href='http://tgbotai.ru/'>Открыть сайт</a>\n\n"
        "Удачи в учебе! 📚"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# ===== Покупка вопросов через Robokassa =====

def generate_shop_links(user_id: int):
    return {
        "💡 1 вопрос — 10₽": create_payment(10, "Покупка 1 вопроса", user_id, 1),
        "🔥 10 вопросов — 90₽": create_payment(90, "Покупка 10 вопросов", user_id, 10),
        "🚀 50 вопросов — 450₽": create_payment(450, "Покупка 50 вопросов", user_id, 50),
        "👑 100 вопросов — 900₽": create_payment(900, "Покупка 100 вопросов", user_id, 100),
    }

@router.message(lambda message: message.text == "💰 Купить вопросы")
async def buy_questions_handler(message: types.Message):
    links = generate_shop_links(message.from_user.id)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in links] + [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )
    text = (
        "💰 <b>Хочешь продолжить обучение?</b>\n\n"
        "Здесь ты можешь купить дополнительные вопросы, если бесплатные закончились.\n\n"
        "🎓 Каждый вопрос приближает тебя к новому статусу!\n"
        "🚀 Больше вопросов → больше знаний → выше XP\n"
        "📈 А ещё Профи и Эксперт получают бонусы и YouTube-видео по теме 🤩\n\n"
        "Выбери пакет ниже ⤵️"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@router.message(lambda message: message.text in generate_shop_links(message.from_user.id))
async def handle_shop_selection(message: types.Message):
    link = generate_shop_links(message.from_user.id)[message.text]
    await message.answer(f"💳 Оплати по ссылке:\n{link}", reply_markup=get_main_keyboard())

