from aiogram import Router
from aiogram.types import Message
from keyboards.shop import get_shop_keyboard

router = Router()

# Показываем главное меню магазина
async def open_shop(message: Message):
    await message.answer(
        "🛒 <b>Добро пожаловать в магазин!</b>\n\nВыберите, что вас интересует:",
        reply_markup=get_shop_keyboard()
    )
