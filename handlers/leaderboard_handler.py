from aiogram import Router, F
from aiogram.types import Message
from services.leaderboard_service import get_leaderboard_text, get_user_position_info
from keyboards.main_menu import get_main_menu_keyboard

router = Router()

@router.message(F.text == "📊 ТОП-10")
async def show_leaderboard(message: Message):
    try:
        with open("leaderboard.txt", "r", encoding="utf-8") as f:
            leaderboard = f.read()
    except FileNotFoundError:
        leaderboard = "Лидерборд пока не сформирован."

    # Получаем позицию пользователя
    user_line = await get_user_position_info(message.from_user.id)

    await message.answer(
        f"<b>🏆 Топ-10 пользователей</b>\n\n{leaderboard}\n\n{user_line}",
        reply_markup=get_main_menu_keyboard(user_id=message.from_user.id)
    )
