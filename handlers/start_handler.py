from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from texts.help_text import HELP_TEXT
from keyboards.main_menu import get_main_menu_keyboard

from handlers.profile_handler import show_profile
from handlers.leaderboard_handler import show_leaderboard
from handlers.missions_handler import show_missions
from handlers.shop_handler import open_shop
from handlers.program_handler import start_program_selection
from handlers.info_handler import show_info_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    keyboard = get_main_menu_keyboard(user_id)
    await message.answer(
        "Привет 👋\n\n"
        "Я — твой Образовательный консультант. Помогаю разобраться в учебных дисциплинах, "
        "выбрать нужную программу и подготовиться к экзаменам вместе с ИИ.\n\n"
        "🧠 Отвечаю строго по теме — если в вопросе нет ключевых слов из выбранной дисциплины, ответа не будет.\n\n"
        "🎯 Каждый вопрос приносит тебе XP (если нет подписки), а XP повышает твой статус и открывает бонусы, миссии и награды.\n"
        "📊 Следи за прогрессом в разделе «Мой профиль», выполняй миссии, получай достижения и бейджи.\n\n"
        "💡 Вопросы заканчиваются? Можно купить новые или оформить подписку.\n"
        "🎥 В подписке Про или Лайт ты получишь доступ к видео и другим бонусам.\n\n"
        "<b>Готов начать? Выбирай действие ⤵️</b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@router.message(F.text == "❓ Помощь")
@router.message(F.text == "/help")
async def show_help(message: Message):
    await message.answer(HELP_TEXT, disable_web_page_preview=True)

@router.message(F.text == "👤 Мой профиль")
async def handle_profile(message: Message):
    await show_profile(message)

@router.message(F.text == "📊 ТОП-10")
async def handle_leaderboard(message: Message):
    await show_leaderboard(message)

@router.message(F.text == "🎯 Миссии")
async def handle_missions(message: Message):
    await show_missions(message)

@router.message(F.text == "🛒 Магазин")
async def handle_shop(message: Message):
    await open_shop(message)

@router.message(F.text == "💬 Выбор программы")
async def handle_program_selection(message: Message):
    await start_program_selection(message)

@router.message(F.text == "ℹ️ Info")
async def handle_info(message: Message):
    await show_info_menu(message)

#@router.message()
#async def fallback(message: Message):
#    await message.answer("Команда не распознана. Напиши /start.")
