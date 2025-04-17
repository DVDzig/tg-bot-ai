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
    print("[DEBUG] handle_photo_with_test called ✅")

    user_id = message.from_user.id
    row = await get_user_row_by_id(user_id)
    if not row:
        await message.answer("Ошибка: не удалось получить данные пользователя.")
        return

    plan = row.get("plan", "").lower()
    status = row.get("status", "").split()[-1]

    if plan != "pro" and status not in ["Эксперт", "Наставник", "Легенда", "Создатель"]:
        await message.answer("🛑 Эта функция доступна только для пользователей со статусом Эксперт+ или подпиской Про.")
        return

    success = await decrease_question_limit(user_id)
    if not success:
        await message.answer("❌ У вас закончились вопросы. Пополните лимит в разделе 🛒 Магазин.")
        return

    await message.answer("📸 Фото получено. Распознаю текст через Google Vision...")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    image_data = await message.bot.download_file(file.file_path)

    try:
        text = extract_text_from_image(image_data)
    except Exception as e:
        print(f"[Vision API ERROR] {e}")
        await message.answer("❗ Не удалось распознать текст с фото. Попробуй позже.")
        return

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"photo_{user_id}_{now}.png"

    upload_image_to_drive(file_name, BytesIO(image_data), folder_id=PHOTO_ARCHIVE_FOLDER_ID)

    if not text.strip():
        await message.answer("❗ Не удалось распознать текст. Проверь, что на фото есть чёткий текст.")
        return

    await message.answer(f"📄 Распознанный текст:\n<pre>{text}</pre>", parse_mode="HTML")

    try:
        answer = await generate_answer("Общий анализ", "Тест", "Фотозапрос", text)
        await message.answer(f"🤖 Ответ ИИ:\n\n{answer}")
        await update_user_after_answer(user_id, bot=message.bot)
        await log_photo_request(user_id, text, answer)
    except Exception as e:
        print(f"[GPT ERROR] {e}")
        await message.answer("⚠️ Не удалось сгенерировать ответ. Попробуй позже.")

    await state.set_state(ProgramSelection.asking)

@router.message(F.photo)
async def reject_photo_outside_context(message: Message, state: FSMContext):
    current = await state.get_state()
    if current != ProgramSelection.asking:
        await message.answer("📸 Фото можно отправлять только в меню общения с ИИ по дисциплине.")
