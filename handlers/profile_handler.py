from aiogram import Router, F
from aiogram.types import Message
from services.user_service import get_user_profile_text

router = Router()


@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    user = message.from_user
    profile_text = await get_user_profile_text(user)
    await message.answer(profile_text)
