from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.shop import get_shop_keyboard

router = Router()

@router.message(F.text == "🛒 Магазин")
async def open_shop(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🛒 <b>Добро пожаловать в магазин!</b>\n\nВыберите, что вас интересует:",
        reply_markup=get_shop_keyboard()
    )
