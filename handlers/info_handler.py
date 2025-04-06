from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from keyboards.info_keyboard import get_info_menu_keyboard
from texts.help_text import HELP_TEXT
from texts.statuses_text import STATUS_TEXT
from texts.subscriptions_text import SUBSCRIPTIONS_TEXT

router = Router()

# Главное меню Info
@router.message(F.text == "ℹ️ Info")
async def show_info_menu(message: Message):
    await message.answer(
        "ℹ️ Выбери, что тебе интересно:",
        reply_markup=get_info_menu_keyboard()
    )

# Статусы
@router.message(F.text == "🎖️ Статусы")
async def show_statuses(message: Message):
    await message.answer(STATUS_TEXT)

# Подписки
@router.message(F.text == "💳 Подписки")
async def show_subscriptions(message: Message):
    await message.answer(SUBSCRIPTIONS_TEXT)

# Помощь
@router.message(F.text == "❓ Помощь")
async def show_help(message: Message):
    await message.answer(HELP_TEXT)
