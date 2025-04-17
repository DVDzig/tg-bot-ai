from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime
from config import PHOTO_ARCHIVE_FOLDER_ID
from io import BytesIO

from services.user_service import get_user_row_by_id, update_user_after_answer, decrease_question_limit
from services.vision_service import extract_text_from_image
from services.google_drive_service import upload_image_to_drive
from services.google_sheets_service import log_photo_request
from services.gpt_service import generate_answer
from states.program_states import ProgramSelection

router = Router()

@router.message(ProgramSelection.asking, F.photo)
async def handle_photo_with_test(message: Message, state: FSMContext):
    print("[DEBUG] 🧠 Вошёл в handle_photo_with_test")

    user_id = message.from_user.id
    print(f"[DEBUG] 📥 user_id = {user_id}")

    row = await get_user_row_by_id(user_id)
    if not row:
        print("[DEBUG] ❌ Пользователь не найден")
        await message.answer("Ошибка: не удалось получить данные пользователя.")
        return

    plan = row.get("plan", "").lower()
    status = row.get("status", "").split()[-1]
    print(f"[DEBUG] 📊 Статус: {status}, План: {plan}")

    if plan != "pro" and status not in ["Эксперт", "Наставник", "Легенда", "Создатель"]:
        print("[DEBUG] ❌ Недостаточный статус")
        await message.answer("🛑 Эта функция доступна только для пользователей со статусом Эксперт+ или подпиской Про.")
        return

    success = await decrease_question_limit(user_id)
    print(f"[DEBUG] ✅ Лимит списан: {success}")
    if not success:
        await message.answer("❌ У вас закончились вопросы. Пополните лимит в разделе 🛒 Магазин.")
        return

    await message.answer("📸 Фото получено. Распознаю текст через Google Vision...")

    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        image_data = await message.bot.download_file(file.file_path)
    except Exception as e:
        print(f"[ERROR] Ошибка при получении фото: {e}")
        await message.answer("⚠️ Не удалось загрузить изображение.")
        return

    try:
        text = extract_text_from_image(image_data)
    except Exception as e:
        print(f"[ERROR] Vision API Error: {e}")
        await message.answer("❗ Не удалось распознать текст. Попробуй позже.")
        return

    await state.set_state(ProgramSelection.asking)  # Устанавливаем состояние обратно в asking
    print("[DEBUG] 🔁 FSM возвращена в asking")

@router.message(F.photo)
async def reject_photo_outside_context(message: Message, state: FSMContext):
    current = await state.get_state()
    print(f"[DEBUG] 🧐 Текущее состояние: {current}")
    if current is None:
        # Иногда FSM может быть сброшен — проверим текст предыдущего сообщения
        await message.answer("📸 Кажется, ты не выбрал дисциплину. Пожалуйста, выбери её перед загрузкой фото.")
    elif current != ProgramSelection.asking:
        await message.answer("📸 Фото можно отправлять только в меню общения с ИИ по дисциплине.")
