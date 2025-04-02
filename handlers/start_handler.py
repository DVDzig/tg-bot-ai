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
from services.missions import get_all_missions
from datetime import datetime

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
        "Я — твой Образовательный консультант. Помогаю разобраться в учебных дисциплинах, выбрать нужную программу и подготовиться к экзаменам вместе с ИИ.\n\n"
        "🧠 Отвечаю строго по теме — если в вопросе нет ключевых слов из выбранной дисциплины, ответа не будет.\n\n"
        "🎯 Каждый вопрос приносит тебе XP (если нет подписки), а XP повышает твой статус и открывает бонусы, миссии и награды.\n"
        "📊 Следи за прогрессом в разделе «Мой профиль», выполняй миссии, получай достижения и бейджи.\n\n"
        "💡 Вопросы заканчиваются? Можно купить новые или оформить подписку.\n"
        "🎥 В статусе Про или при подписке ты получишь доступ к видео и другим бонусам.\n\n"
        "Готов начать? Выбирай действие ⤵️"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

async def go_to_start_screen(message: types.Message):
    text = (
        "📚 Главное меню готово!\n\n"
        "❓ Задавай вопросы по выбранной дисциплине и получай XP\n"
        "🎯 Выполняй миссии (ежедневные, недельные, стрики) — и получай бонусы\n"
        "🏆 Повышай статус, открывай возможности и собирай достижения\n"
        "💳 Закончились вопросы? Купи пакет или оформи подписку\n"
        "🎥 Подписка Про — это +100 вопросов, видео и приоритет\n\n"
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
        + (
            f"\n💎 <b>Активный доступ:</b> {profile_data['premium_status'].capitalize()} "
            f"(до {profile_data.get('premium_until', 'неизвестно')})"
            if profile_data.get("premium_status") in ("light", "pro")
            else ""
        )
    )

    # Добавим предложение купить Лайт или Про, если их нет
    if profile_data.get("premium_status") in (None, "", "none"):
        profile_text += (
            "\n\n🔓 <b>Хочешь больше возможностей?</b>\n\n"
            "• <b>Лайт</b> — безлимит на 7 дней\n"
            "• <b>Про</b> — 100 вопросов, видео и приоритет 🤖\n\n"
            "👉 Доступно в разделе <b>«Купить доступ»</b>"
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
        "Я — твой образовательный консультант. Помогаю изучать дисциплины и готовиться к экзаменам с помощью ИИ.\n\n"
        "❓ <b>Как использовать?</b>\n"
        "1. Выбери образовательную программу и дисциплину.\n"
        "2. Задавай вопросы строго по выбранной теме.\n"
        "3. Получай структурированные и точные ответы.\n\n"
        "📌 <b>Как задавать вопросы правильно?</b>\n"
        "• Вопрос должен быть чётко сформулирован.\n"
        "• Он должен содержать ключевые слова из дисциплины.\n"
        "• Не задавай общих или отвлечённых вопросов — бот ответит только по теме.\n"
        "• Если нет ключевых слов, бот не даст ответ.\n\n"
        "<b>Примеры:</b>\n"
        "✅ <i>«Какие методы используются в медиапланировании?»</i>\n"
        "✅ <i>«Что включает в себя спортивный контент?»</i>\n"
        "❌ <i>«Расскажи что-нибудь»</i>\n"
        "❌ <i>«Привет, как дела?»</i>\n\n"
        "💡 <b>Дополнительно:</b>\n"
        "• За каждый вопрос ты получаешь XP (если нет подписки).\n"
        "• В разделе <b>ℹ️ Статусы и подписки</b> — всё про уровни, миссии, бонусы и подписки.\n\n"
        "📄 <b>Условия использования и оплата:</b>\n"
        "<a href='http://tgbotai.ru/'>Открыть сайт</a>\n\n"
        "Удачи в учёбе и приятной прокачки! 📚"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# ===== Покупка вопросов через Robokassa =====

def generate_shop_links(user_id: int):
    return {
        "💡 Лайт-доступ — 149₽": create_payment(149, "Покупка статуса Лайт", user_id, questions=30, status="light"),
        "🚀 Про-доступ — 299₽": create_payment(299, "Покупка статуса Про", user_id, questions=100, status="pro"),
        "💡 1 вопрос — 10₽": create_payment(10, "Покупка 1 вопроса", user_id, 1),
        "🔥 10 вопросов — 90₽": create_payment(90, "Покупка 10 вопросов", user_id, 10),
        "🚀 50 вопросов — 450₽": create_payment(450, "Покупка 50 вопросов", user_id, 50),
        "👑 100 вопросов — 900₽": create_payment(900, "Покупка 100 вопросов", user_id, 100),
   }


@router.message(lambda message: message.text == "🛍 Магазин")
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

def get_shop_keyboard():
    keyboard = [
        [KeyboardButton(text="💰 Купить вопросы")],
        [KeyboardButton(text="💡 Лайт-доступ — 149₽")],
        [KeyboardButton(text="🚀 Про-доступ — 299₽")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(lambda msg: msg.text == "ℹ️ Статусы и подписки")
async def show_status_info(message: types.Message):
    await message.answer(
        "🎖 <b>Система статусов</b>\n"
        "Задавай вопросы, выполняй миссии и получай XP — прокачивай свой статус!\n\n"
        "🟢 <b>Новичок</b> — 0–10 XP (+5 вопросов в месяц)\n"
        "🔸 <b>Опытный</b> — 11–50 XP (+10 в месяц)\n"
        "🚀 <b>Профи</b> — 51–150 XP (+20 в месяц, открывается новый интерфейс)\n"
        "👑 <b>Эксперт</b> — 151–300 XP (+30 в месяц, доступ к генерации изображений DALL·E)\n"
        "🧠 <b>Наставник</b> — 301–999 XP (+50 в месяц, NFT-бейджи)\n"
        "🎓 <b>Легенда</b> — 1000–4999 XP (+75 в месяц)\n"
        "🛸 <b>Создатель</b> — 5000+ XP (+100 в месяц)\n\n"
        "📈 <b>Бонусы за активность:</b>\n"
        "• Каждые 100 XP — дополнительный бесплатный вопрос 🎁\n"
        "• Стрик 7 и 14 дней — ещё больше бонусов 🔥\n\n"
        "🎯 <b>Миссии:</b>\n"
        "• Ежедневные — например, 3 вопроса или 3 дисциплины в день\n"
        "• Недельные — 10 вопросов, 50 XP, 5 дисциплин и другие\n"
        "• Стрик-миссии — не пропускай дни и получай награды\n\n"
        "🏆 <b>Достижения:</b>\n"
        "• Сохраняются навсегда и открывают уникальные бейджи\n"
        "• Например: Первый вопрос, 100 XP, 10 миссий подряд и др.\n\n"
        "💳 <b>Подписки:</b>\n"
        "• 💡 <b>Лайт</b> — безлимит на 7 дней, XP не начисляется\n"
        "• 🚀 <b>Про</b> — безлимит, +100 вопросов, видео, приоритетный режим, DALL·E, отключение ограничений\n\n"
        "🔐 <i>Подписки отключают лимиты и дают доступ к новым возможностям</i>\n"
        "🔥 <i>Прокачивайся, побеждай и попади в Легенды!</i>",
        parse_mode="HTML"
    )


@router.message(lambda msg: msg.text == "🎯 Миссии")
async def show_missions(message: types.Message):
    user_id = message.from_user.id
    profile = get_user_profile(user_id)
    today_str = datetime.now().strftime("%d.%m.%Y")

    lines = ["🎯 <b>Твои миссии на сегодня:</b>\n"]

    for mission in get_all_missions():
        last_key = f"last_{mission.id}"
        last_done = profile.get(last_key, "")

        if last_done == today_str:
            status = "✅ Выполнено"
        else:
            status = "⏳ В процессе"

        lines.append(f"{mission.title} — {status} (+{mission.reward} XP)")

    await message.answer("\n".join(lines), parse_mode="HTML")