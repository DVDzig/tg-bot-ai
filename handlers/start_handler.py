from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from texts.help_text import HELP_TEXT

from keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
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
        reply_markup=get_main_menu_keyboard(message.from_user.id)
    )

@router.message(F.text == "❓ Помощь")
@router.message(F.text == "/help")
async def show_help(message: Message):
    await message.answer(HELP_TEXT, disable_web_page_preview=True)