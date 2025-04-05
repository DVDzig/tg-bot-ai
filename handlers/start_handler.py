from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.keyboard import get_main_keyboard, get_question_packages_keyboard, get_subscription_packages_keyboard, get_shop_keyboard
from services.user_service import (
    apply_xp_penalty_if_needed,
    get_user_activity_stats,
    determine_status,
    get_user_profile_from_row, 
    get_or_create_user,
    get_user_row
)
from services.google_sheets_service import get_leaderboard, get_sheet_data
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, Message
from services.yookassa_service import create_payment
from config import USER_SHEET_ID
from services.missions import get_all_missions
from datetime import datetime
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable


router = Router()

def get_welcome_text():
    return (
        "Привет 👋\n\n"
        "Я — твой Образовательный консультант. Помогаю разобраться в учебных дисциплинах, выбрать нужную программу и подготовиться к экзаменам вместе с ИИ.\n\n"
        "🧠 Отвечаю строго по теме — если в вопросе нет ключевых слов из выбранной дисциплины, ответа не будет.\n\n"
        "🎯 Каждый вопрос приносит тебе XP (если нет подписки), а XP повышает твой статус и открывает бонусы, миссии и награды.\n"
        "📊 Следи за прогрессом в разделе «Мой профиль», выполняй миссии, получай достижения и бейджи.\n\n"
        "💡 Вопросы заканчиваются? Можно купить новые или оформить подписку.\n"
        "🎥 В статусе Про или при подписке ты получишь доступ к видео и другим бонусам.\n\n"
        "Готов начать? Выбирай действие ⤵️"
    )

def get_main_screen_text():
    return (
        "📚 Главное меню готово!\n\n"
        "❓ Задавай вопросы по выбранной дисциплине и получай XP\n"
        "🎯 Выполняй миссии (ежедневные, недельные, стрики) — и получай бонусы\n"
        "🏆 Повышай статус, открывай возможности и собирай достижения\n"
        "💳 Закончились вопросы? Купи пакет или оформи подписку\n"
        "🎥 Подписка Про — это +100 вопросов, видео и приоритет\n\n"
        "Выбери действие ниже ⤵️"
    )

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
    await message.answer(get_welcome_text(), reply_markup=get_main_keyboard())

async def go_to_start_screen(message: types.Message):
    await message.answer(get_main_screen_text(), reply_markup=get_main_keyboard())

# === Мой профиль ===
@router.message(lambda message: message.text == "👤 Мой профиль")
async def profile_handler(message: types.Message):
    user_id = message.from_user.id
    # Заменили: теперь передаем данные пользователя, а не его ID
    profile = get_user_profile_from_row(get_user_row(user_id)[1])
    stats = get_user_activity_stats(user_id)
    current_xp = profile['xp']
    current_status, next_status, xp_to_next = determine_status(current_xp)

    # Прогресс
    thresholds = {
        "новичок": (0, 10),
        "опытный": (11, 50),
        "профи": (51, 100),
        "эксперт": (101, 150)
    }
    min_xp, max_xp = thresholds.get(current_status, (0, 10))
    progress = 100 if current_xp >= max_xp else int(((current_xp - min_xp) / (max_xp - min_xp)) * 100)
    bar_blocks = min(5, int(progress / 5))
    progress_bar = "🟩" * bar_blocks + "⬜️" * (5 - bar_blocks)

    # Покупки
    last_purchase_text = ""
    for row in reversed(get_sheet_data(USER_SHEET_ID, "PaymentsLog!A2:G")):
        if row[0] == str(user_id) and row[4] == "payment.succeeded":
            q_count, price, date = row[2], row[1], row[6]
            last_purchase_text = f"\n🧾 <b>Последняя покупка:</b>\n• {q_count} вопрос(ов), {price}₽\n• {date}"
            break

    challenge_text = (
        f"🔥 Сегодня ты уже задал {stats['today']} из 3 вопросов!"
        if stats['today'] < 3
        else "🏆 Ты выполнил ежедневный челлендж!"
    )

    premium = profile.get("premium_status", "")
    premium_text = ""
    if premium in ("light", "pro"):
        until = profile.get("premium_until", "неизвестно")
        premium_text = f"\n💎 <b>Активный доступ:</b> {premium.capitalize()} (до {until})"

    profile_text = (
        f"👤 <b>Имя:</b> {profile['first_name']}\n"
        f"🎖️ <b>Статус:</b> {current_status.capitalize()} — {progress_bar} {progress}%\n"
        f"⭐ <b>Твой XP:</b> {current_xp} XP\n"
        f"📅 <b>Последний вход:</b> {profile['last_interaction']}\n\n"
        f"🎁 <b>Доступные вопросы:</b>\n"
        f"• Бесплатные: {profile['free_questions']}\n"
        f"• Платные: {profile['paid_questions']}"
        f"{last_purchase_text}\n\n"
        f"📈 <b>Активность:</b>\n"
        f"• Сегодня: {stats['today']} вопрос(ов)\n"
        f"• За неделю: {stats['week']} вопрос(ов)\n"
        f"• Всего: {stats['total']} вопрос(ов)\n\n"
        f"{challenge_text}\n\n"
        + (
            f"💡 <i>Ближайший статус:</i> {next_status} (ещё {xp_to_next} XP)\n"
            if next_status != "максимальный"
            else "🎓 Ты уже достиг максимального уровня! Поздравляем! 🏆\n"
        )
        + premium_text
    )

    if premium in ("", "none", None):
        profile_text += (
            "\n\n🔓 <b>Хочешь больше возможностей?</b>\n\n"
            "• <b>Лайт</b> — безлимит на 7 дней\n"
            "• <b>Про</b> — 100 вопросов, видео и приоритет 🤖\n\n"
            "👉 Доступно в разделе <b>«Купить доступ»</b>"
        )

    await message.answer(profile_text, parse_mode="HTML", reply_markup=get_main_keyboard())


# === Лидерборд ===
@router.message(lambda msg: msg.text == "📊 Лидерборд")
async def leaderboard_handler(message: types.Message):
    leaderboard = get_leaderboard(top_n=100)
    if not leaderboard:
        await message.answer("🏆 Пока что нет пользователей в рейтинге.")
        return

    user_id = str(message.from_user.id)
    # Получаем строку данных пользователя
    row = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    row = next((r for r in row if r[0] == user_id), None)  # Получаем строку с данными

    if row is None:
        await message.answer("❌ Не найден пользователь в базе данных.")
        return

    profile = get_user_profile_from_row(row)  # Передаем строку
    current_xp = profile["xp"]
    current_status, next_status, xp_target = determine_status(current_xp)

    status_icons = {
        "новичок": "🟢", "опытный": "🔸", "профи": "🚀", "эксперт": "👑",
        "наставник": "🧠", "легенда": "🎓", "создатель": "🛸"
    }

    top_text = "🏆 <b>Топ-10 пользователей по XP</b>:\n\n"
    user_place = None
    for idx, entry in enumerate(leaderboard[:10], start=1):
        name = entry.get("first_name") or f"@{entry.get('username', 'неизвестно')}"
        entry_status, _, _ = determine_status(entry["xp"])
        icon = status_icons.get(entry_status, "❓")
        place_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, f"{idx}.")
        is_you = " (ты)" if entry["user_id"] == user_id else ""
        top_text += f"{place_emoji} {name} — {icon} {entry_status.capitalize()}, {entry['xp']} XP{is_you}\n"

    for idx, entry in enumerate(leaderboard, start=1):
        if str(entry["user_id"]) == str(user_id):
            user_place = idx
            break

    if user_place is None:
        tail = "\n👤 Ты пока не в рейтинге. Начни задавать вопросы — и попадёшь в топ! 🏁"
    else:
        tail = f"\n👤 Ты сейчас на {user_place} месте"
        if current_status == "создатель":
            tail += "\n🛸 Ты достиг вершины! Легенда среди легенд 👑"
        else:
            xp_left = max(0, xp_target - current_xp)
            tail += f"\n📈 До уровня «{next_status}» осталось {xp_left} XP\nПродолжай в том же духе! 💪"

    await message.answer(top_text + tail, parse_mode="HTML")

# === Миссии ===
@router.message(lambda msg: msg.text == "🎯 Миссии")
async def show_missions(message: types.Message):
    user_id = message.from_user.id
    profile = get_user_profile_from_row(user_id)
    today = datetime.now().strftime("%d.%m.%Y")

    lines = ["🎯 <b>Твои миссии на сегодня:</b>\n"]
    for mission in get_all_missions():
        key = f"last_{mission.id}"
        done_today = profile.get(key, "") == today
        status = "✅ Выполнено" if done_today else "⏳ В процессе"
        lines.append(f"{mission.title} — {status} (+{mission.reward} XP)")

    await message.answer("\n".join(lines), parse_mode="HTML")

# === Помощь ===
def get_help_text():
    return (
        "ℹ️ <b>О боте</b>\n"
        "Я — твой образовательный консультант. Помогаю изучать дисциплины и готовиться к экзаменам с помощью ИИ.\n\n"
        "❓ <b>Как использовать?</b>\n"
        "1. Выбери образовательную программу и дисциплину.\n"
        "2. Задавай вопросы строго по выбранной теме.\n"
        "3. Получай структурированные и точные ответы.\n\n"
        "📌 <b>Как задавать вопросы правильно?</b>\n"
        "• Вопрос должен быть чётко сформулирован.\n"
        "• Он должен содержать ключевые слова из дисциплины.\n"
        "• Не задавай общих или отвлечённых вопросов — бот ответит только по теме.\n\n"
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

@router.message(lambda m: m.text and "помощь" in m.text.lower())
async def help_handler(message: types.Message):
    await message.answer(get_help_text(), parse_mode="HTML", reply_markup=get_main_keyboard())

# === Генерация платёжных ссылок через YooKassa ===

def generate_shop_links(user_id: int):
    return {
        "💡 Лайт-доступ — 149₽": create_payment(149, "Покупка статуса Лайт", user_id, questions=30, status="light"),
        "🚀 Про-доступ — 299₽": create_payment(299, "Покупка статуса Про", user_id, questions=100, status="pro"),
        "💡 1 вопрос — 10₽": create_payment(10, "Покупка 1 вопроса", user_id, 1),
        "🔥 10 вопросов — 90₽": create_payment(90, "Покупка 10 вопросов", user_id, 10),
        "🚀 50 вопросов — 450₽": create_payment(450, "Покупка 50 вопросов", user_id, 50),
        "👑 100 вопросов — 900₽": create_payment(900, "Покупка 100 вопросов", user_id, 100),
    }

@router.message(lambda message: message.text in generate_shop_links(message.from_user.id))
async def handle_shop_selection(message: types.Message):
    link = generate_shop_links(message.from_user.id)[message.text]
    await message.answer(f"💳 Оплати по ссылке:\n{link}", reply_markup=get_main_keyboard())

# === Покупка вопросов ===
@router.message(lambda msg: msg.text and msg.text.strip() == "💬 Вопросы")
async def handle_question_shop(message: types.Message):
    await message.answer(
        "💬 <b>Покупка вопросов</b>\n\n"
        "Если у тебя закончились бесплатные вопросы — просто купи дополнительные и продолжай обучение!\n\n"
        "📌 Зачем это нужно:\n"
        "• Получай ответы от ИИ по учебным дисциплинам\n"
        "• XP будет начисляться за каждый вопрос\n"
        "• Возможность прокачиваться, выполнять миссии, открывать достижения\n\n"
        "Выбери нужный пакет ниже 👇",
        parse_mode="HTML",
        reply_markup=get_question_packages_keyboard()
    )

# === Подписка ===
@router.message(lambda msg: msg.text == "💳 Подписка")
async def handle_subscription_shop(message: types.Message):
    await message.answer(
        "💳 <b>Подписка</b>\n\n"
        "Подписка снимает все лимиты и даёт доступ к эксклюзивным функциям!\n\n"
        "🎁 Что даёт подписка:\n"
        "• Безлимит на вопросы (не тратятся, XP не начисляется)\n"
        "• 🚀 Про: +100 вопросов, видео, генерация изображений, приоритет\n"
        "• 💡 Лайт: просто безлимит на неделю\n\n"
        "Выбирай нужный тариф ниже 👇",
        parse_mode="HTML",
        reply_markup=get_subscription_packages_keyboard()
    )
    
@router.message(F.text == "⬅️ Назад")
async def handle_back_button(message: types.Message):
    # Простая логика — определяем по последнему сообщению пользователя
    text = message.text or ""

    # Используем контекст предыдущего экрана — из словаря, если был переход
    if message.reply_to_message and message.reply_to_message.text:
        last_text = message.reply_to_message.text
    else:
        last_text = ""

    if any(phrase in last_text for phrase in ["Выбери нужный пакет", "Выбирай нужный тариф"]):
        await message.answer(
            "🔙 Возврат в магазин.\n\nВыбери, что тебя интересует 👇",
            reply_markup=get_shop_keyboard()
        )
    elif "Выбери, что тебя интересует" in last_text:
        await message.answer(
            "🔙 Возврат в главное меню",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer("🔙 Главное меню", reply_markup=get_main_keyboard())

# === Инфо о статусах и подписках ===
@router.message(lambda msg: msg.text == "ℹ️ Статусы и подписки")
async def show_status_info(message: types.Message):
    await message.answer(
        "🎖 <b>Система статусов</b>\n"
        "Задавай вопросы, выполняй миссии и получай XP — прокачивай свой статус!\n\n"
        "🟢 <b>Новичок</b> — 0–10 XP (+5 вопросов в месяц)\n"
        "🔸 <b>Опытный</b> — 11–50 XP (+10 в месяц)\n"
        "🚀 <b>Профи</b> — 51–150 XP (+20 в месяц, новый интерфейс)\n"
        "👑 <b>Эксперт</b> — 151–300 XP (+30 в месяц, доступ к DALL·E)\n"
        "🧠 <b>Наставник</b> — 301–999 XP (+50 в месяц, NFT-бейджи)\n"
        "🎓 <b>Легенда</b> — 1000–4999 XP (+75 в месяц)\n"
        "🛸 <b>Создатель</b> — 5000+ XP (+100 в месяц)\n\n"
        "📈 <b>Бонусы за активность:</b>\n"
        "• Каждые 100 XP — дополнительный бесплатный вопрос 🎁\n"
        "• Стрик 7 и 14 дней — ещё больше бонусов 🔥\n\n"
        "🎯 <b>Миссии:</b>\n"
        "• Ежедневные — 3 вопроса, 3 дисциплины в день\n"
        "• Недельные — 10 вопросов, 50 XP, 5 дисциплин и др.\n"
        "• Стрик-миссии — не пропускай дни и получай награды\n\n"
        "🏆 <b>Достижения:</b>\n"
        "• Первый вопрос, 100 XP, 10 миссий подряд и др.\n\n"
        "💳 <b>Подписки:</b>\n"
        "• 💡 Лайт — безлимит на 7 дней, XP не начисляется\n"
        "• 🚀 Про — всё из Лайт + видео, 100 вопросов, приоритет\n\n"
        "🔐 Подписки отключают лимиты и дают больше возможностей!\n"
        "🔥 Прокачивайся и попади в Легенды!",
        parse_mode="HTML"
    )


@router.message(lambda msg: msg.text == "🎯 Миссии")
async def show_missions(message: types.Message):
    user_id = message.from_user.id
    profile = get_user_profile_from_row(user_id)
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
    
@router.message(lambda msg: msg.text and msg.text.strip() == "💬 Вопросы")
async def handle_question_shop(message: types.Message):
    print("[DEBUG] Кнопка ВОПРОСЫ сработала")
    await message.answer(
        "💬 <b>Покупка вопросов</b>\n\n"
        "Если у тебя закончились бесплатные вопросы — просто купи дополнительные и продолжай обучение!\n\n"
        "📌 Зачем это нужно:\n"
        "• Получай ответы от ИИ по учебным дисциплинам\n"
        "• XP будет начисляться за каждый вопрос\n"
        "• Возможность прокачиваться, выполнять миссии, открывать достижения\n\n"
        "Выбери нужный пакет ниже 👇",
        parse_mode="HTML",
        reply_markup=get_question_packages_keyboard()
    )
@router.message(lambda msg: msg.text == "💳 Подписка")
async def handle_subscription_shop(message: types.Message):
    await message.answer(
        "💳 <b>Подписка</b>\n\n"
        "Подписка снимает все лимиты и даёт доступ к эксклюзивным функциям!\n\n"
        "🎁 Что даёт подписка:\n"
        "• Безлимит на вопросы (не тратятся, XP не начисляется)\n"
        "• 🚀 Про: +100 вопросов, видео, генерация изображений, приоритет\n"
        "• 💡 Лайт: просто безлимит на неделю\n\n"
        "Выбирай нужный тариф ниже 👇",
        parse_mode="HTML",
        reply_markup=get_subscription_packages_keyboard()
    )

class EnsureUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        get_or_create_user(
            user_id=user.id,
            username=user.username or "Unknown",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            language_code=user.language_code or "",
            is_premium=getattr(user, "is_premium", False)
        )
        return await handler(event, data)
