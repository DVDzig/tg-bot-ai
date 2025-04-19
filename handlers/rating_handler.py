from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.google_sheets_service import log_user_rating
from services.user_service import get_user_row_by_id
from aiogram.fsm.context import FSMContext

router = Router()

@router.callback_query(F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    print(f"[DEBUG] Callback data: {callback.data}")
    rating = callback.data.split(":")[1]
    user = callback.from_user

    row = await get_user_row_by_id(user.id)
    if row:
        xp = int(row.get("xp", 0))
        status = row.get("status", "Новичок")
        await log_user_rating(user.id, rating, status, xp)

    await callback.answer("Спасибо за оценку!", show_alert=False)
