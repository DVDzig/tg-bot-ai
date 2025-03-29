from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from utils.keyboard import get_main_keyboard
from services.user_service import get_user_profile, get_or_create_user
from services.user_service import (
    apply_xp_penalty_if_needed,
    get_user_activity_stats,
    determine_status
)
from services.google_sheets_service import get_leaderboard
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.markdown import hlink
from hashlib import md5
from config import robokassa_links as old_links
from urllib.parse import quote

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
        "Я — ИИ-консультант, помогу в подготовке к любой дисциплине твоей образовательной программы.\n\n"
        "🎯 За каждый вопрос ты получаешь XP и растешь в статусе:\n"
        "🟢 Новичок — 0 - 10 XP\n"
        "🔸 Опытный — 11 – 50 XP\n"
        "🚀 Профи — 51 - 100 XP\n"
        "👑 Эксперт — 101+ XP\n\n"
        "💰 Нужно больше вопросов? Купи дополнительные в личном кабинете.\n"
        "⚠️ Важно: если вопрос не по теме дисциплины — ответа не будет.\n\n"
        "Выбери действие ниже ⤵️"
    )
    markup = get_main_keyboard()
    await message.answer(welcome_text, reply_markup=markup)

# Обработчик для кнопки "Мой профиль"
@router.message(lambda message: message.text.lower() == "👤 мой профиль")
async def profile_handler(message: types.Message):
    user_id = message.from_user.id

    profile_data = get_user_profile(user_id)
    stats = get_user_activity_stats(user_id)

    current_xp = profile_data['xp']
    new_status, _ = determine_status(current_xp)

    thresholds = {
        "новичок": (0, 10),
        "опытный": (11, 50),
        "профи": (51, 100),
        "эксперт": (101, 150)
    }
    min_xp, max_xp = thresholds.get(new_status, (0, 10))
    progress = int(((current_xp - min_xp) / (max_xp - min_xp)) * 100) if max_xp > min_xp else 100
    bar_blocks = min(5, int(progress / 5))
    progress_bar = "🟩" * bar_blocks + "⬜️" * (5 - bar_blocks)
    progress_display = f"{progress_bar} {progress}%"

    daily_goal = 3
    challenge_text = (
        f"🔥 Сегодня ты уже задал {stats['today']} из {daily_goal} вопросов!"
        if stats['today'] < daily_goal
        else "🏆 Ты выполнил ежедневный челлендж!"
    )

    profile_text = (
        f"👤 <b>Имя:</b> {profile_data['first_name']}\n"
        f"🎖️ <b>Статус:</b> {new_status.capitalize()}\n"
        f"⭐ <b>XP:</b> {current_xp} (прогресс: {progress_display})\n"
        f"📅 <b>Последний вход:</b> {profile_data['last_interaction']}\n"
        f"🎁 <b>Бесплатные вопросы:</b> {profile_data['free_questions']}\n"
        f"💰 <b>Платные вопросы:</b> {profile_data['paid_questions']}\n\n"
        f"📈 <b>История активности:</b>\n"
        f"• Сегодня: {stats['today']} вопрос(ов)\n"
        f"• За неделю: {stats['week']} вопрос(ов)\n"
        f"• Всего: {stats['total']} вопрос(ов)\n\n"
        f"{challenge_text}"
    )

    await message.answer(profile_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# Обработка кнопки "📊 Лидерборд"
@router.message(lambda msg: msg.text == "📊 Лидерборд")
async def leaderboard_handler(message: types.Message):
    leaderboard = get_leaderboard(top_n=10)
    if not leaderboard:
        await message.answer("🏆 Пока что нет пользователей в рейтинге.")
        return

    user_id = str(message.from_user.id)
    text = "🏆 <b>Топ-10 пользователей по XP</b>:\n\n"
    for idx, entry in enumerate(leaderboard, start=1):
        name = entry.get("first_name") or f"@{entry.get('username', 'неизвестно')}"
        highlight = " (ты)" if entry['user_id'] == user_id else ""

        status, _ = determine_status(entry['xp'])
        status_icon = {
            "новичок": "🟢",
            "опытный": "🔸",
            "профи": "🚀",
            "эксперт": "👑"
        }.get(status, "❓")

        text += f"{idx}. {name} — {status_icon} {entry['xp']} XP{highlight}\n"

    await message.answer(text, parse_mode="HTML")

# Обработчик для кнопки "ℹ️ Помощь"
@router.message(lambda m: m.text and "помощь" in m.text.lower())
async def help_handler(message: types.Message):
    help_text = (
        "ℹ️ <b>О боте</b>\n"
        "Я — ИИ-консультант по учебным дисциплинам. Помогаю готовиться к экзаменам.\n\n"
        "❓ <b>Как это работает?</b>\n"
        "• Задаешь вопросы по выбранной дисциплине — получаешь ответ.\n"
        "• За каждый вопрос ты получаешь 1 XP (очки активности).\n"
        "• XP повышают твой статус и открывают бонусы.\n\n"
        "🏆 <b>Статусы и XP</b>\n"
        "• 🐣 Новичок 0–10 XP\n"
        "• 🎯 Опытный 11–50 XP\n"
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
        "<a href='https://project12671307.tilda.ws/'>Открыть сайт</a>\n\n"
        "Удачи в учебе! 📚"
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

# Функция для генерации подписанной и корректно закодированной ссылки Robokassa
def robokassa_link(amount: int, questions: int, user_id: int) -> str:
    login = "TGTutorBot"
    password1 = "iP540dCVN006A3Ul"
    inv_id = f"{user_id}_{questions}"
    description = f"Buy {questions} Q"
    encoded_description = quote(description)

    signature_raw = f"{login}:{amount}:{inv_id}:{password1}"
    signature = md5(signature_raw.encode()).hexdigest()

    return (
        f"https://auth.robokassa.ru/Merchant/Index.aspx?"
        f"MerchantLogin={login}&OutSum={amount}&InvId={inv_id}&"
        f"Description={encoded_description}&"
        f"Shp_Questions={questions}&Shp_UserID={user_id}&"
        f"SignatureValue={signature}"
    )

# Словарь с динамически сгенерированными ссылками
def generate_shop_links(user_id: int):
    return {
        "1 вопрос — 10₽": robokassa_link(10, 1, user_id),
        "10 вопросов — 90₽": robokassa_link(90, 10, user_id),
        "50 вопросов — 450₽": robokassa_link(450, 50, user_id),
        "100 вопросов — 900₽": robokassa_link(900, 100, user_id),
    }

# Обработчик кнопки "Купить вопросы"
@router.message(lambda message: message.text == "💰 Купить вопросы")
async def buy_questions_handler(message: types.Message):
    links = generate_shop_links(message.from_user.id)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)] for label in links] + [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )
    await message.answer("Выбери нужный пакет вопросов:", reply_markup=keyboard)

# Обработчик выбора количества
@router.message(lambda message: message.text in generate_shop_links(message.from_user.id))
async def handle_shop_selection(message: types.Message):
    link = generate_shop_links(message.from_user.id)[message.text]
    await message.answer(f"💳 Оплати по ссылке:\n{link}", reply_markup=get_main_keyboard())

# Обработчик кнопки "⬅️ Назад"
@router.message(lambda message: message.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Ты в главном меню", reply_markup=get_main_keyboard())
