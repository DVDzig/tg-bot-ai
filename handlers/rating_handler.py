from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.user_service import get_user_row_by_id
from services.google_sheets_service import log_user_rating
from keyboards.common import get_consultant_keyboard

router = Router()


@router.callback_query(F.data.startswith("rating:"))
async def handle_rating(callback: CallbackQuery, state):
    rating = callback.data.split(":")[1]
    user = callback.from_user

    print(f"[DEBUG] Оценка нажата: {rating} от пользователя {user.id} ({user.full_name})")

    row = await get_user_row_by_id(user.id)
    if row:
        xp = int(row.get("xp", 0))
        status = row.get("status", "Новичок")
        plan = row.get("plan", "").strip().lower()
        status_clean = status.split()[-1] if status else "Новичок"

        print(f"[DEBUG] Статус: {status} | XP: {xp} | Plan: {plan}")

        try:
            await log_user_rating(user.id, rating, status, xp)
            print(f"[LOG] Успешно записано в Feedback: {user.id}, {rating}")
        except Exception as e:
            print(f"[ERROR] Ошибка при логировании оценки: {e}")

        await callback.message.answer(
            "📩 Спасибо за твою оценку!",
            reply_markup=get_consultant_keyboard(status_clean, plan)
        )

    else:
        print(f"[WARNING] Пользователь {user.id} не найден в таблице.")

    await callback.answer("Спасибо за оценку!", show_alert=False)
