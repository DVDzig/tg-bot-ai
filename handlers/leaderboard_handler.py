from aiogram import Router, F
from aiogram.types import Message
from services.leaderboard_service import get_leaderboard_text, get_user_position_info
from keyboards.main_menu import get_main_menu_keyboard

router = Router()

@router.message(F.text == "📊 ТОП-10")
async def show_leaderboard(message: Message):
    leaderboard = await get_leaderboard_text(message.from_user.id)
    user_line = await get_user_position_info(message.from_user.id)

    await message.answer(
        f"{leaderboard}\n\n{user_line}",
        reply_markup=get_main_menu_keyboard(user_id=message.from_user.id)
    )
