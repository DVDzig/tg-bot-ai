from aiogram import Router, F
from aiogram.types import Message
from services.missions_service import get_user_missions_text

router = Router()


@router.message(F.text == "🎯 Миссии")
async def show_missions(message: Message):
    missions_text = await get_user_missions_text(message.from_user.id)
    await message.answer(missions_text)
