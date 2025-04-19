from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from services.user_service import get_user_row_by_id
from services.google_sheets_service import log_user_rating
from keyboards.common import get_consultant_keyboard

router = Router()

@router.callback_query(F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state: FSMContext):
    rating = callback.data.split(":")[1]
    user = callback.from_user

    print(f"[DEBUG] Рейтинг получен: {user.id} — {rating}")

    row = await get_user_row_by_id(user.id)
    if row:
        xp = int(row.get("xp", 0))
        status = row.get("status", "Новичок")
        plan = row.get("plan", "").strip().lower()
        status_clean = status.split()[-1] if status else "Новичок"

        await log_user_rating(user.id, rating, status, xp)

        await callback.message.answer(
            "📩 Спасибо за твою оценку!",
            reply_markup=get_consultant_keyboard(status_clean, plan)
        )

    await callback.answer("Спасибо за оценку!", show_alert=False)
