from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from io import BytesIO
from datetime import datetime
from config import PHOTO_ARCHIVE_FOLDER_ID

from services.user_service import (
    get_user_row_by_id,
    decrease_question_limit,
    update_user_after_answer,
)
from services.google_drive_service import upload_image_to_drive
from services.google_sheets_service import log_photo_request
from services.gpt_service import generate_answer
from services.vision_service import extract_text_with_docs_ocr
from states.program_states import ProgramSelection

router = Router()

@router.message(F.photo)
async def handle_photo_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    print(f"[DEBUG] 📥 Получено фото от пользователя {user_id}")

    await message.answer("📸 Фото получено. Распознаю текст...")

    try:
        # Получаем изображение
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        image_data = await message.bot.download_file(file.file_path)
        image_bytes = image_data.read()
        print("[DEBUG] 📷 Фото скачано")
    except Exception as e:
        print(f"[ERROR] Ошибка при получении фото: {e}")
        await message.answer("⚠️ Не удалось загрузить изображение.")
        return

    try:
        # Распознаём текст
        text = extract_text_with_docs_ocr(BytesIO(image_bytes))
        print(f"[DEBUG] 📝 Распознанный текст: {text}")
    except Exception as e:
        print(f"[ERROR] OCR Error: {e}")
        await message.answer("❗ Не удалось распознать текст. Попробуй позже.")
        return

    if not text.strip():
        await message.answer("🔍 На фото не найден текст.")
        return

    await message.answer(f"📄 Распознанный текст:\n<pre>{text}</pre>", parse_mode="HTML")

    # Получаем данные пользователя
    row = await get_user_row_by_id(user_id)
    if not row:
        await message.answer("❗ Не удалось получить данные пользователя.")
        return

    plan = row.get("plan", "").lower()
    status = row.get("status", "").split()[-1]

    # Проверка доступа
    if plan != "pro" and status not in ["Эксперт", "Наставник", "Легенда", "Создатель"]:
        await message.answer("🛑 Фото-вопросы доступны только для статуса Эксперт+ или подписки Про.")
        return

    # Проверка лимита
    success = await decrease_question_limit(user_id)
    if not success:
        await message.answer("❌ У тебя закончились вопросы. Пополни в 🛒 Магазине.")
        return

    # Сохраняем фото на Google Диск
    try:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"photo_{user_id}_{now}.png"
        upload_image_to_drive(file_name, BytesIO(image_bytes), folder_id=PHOTO_ARCHIVE_FOLDER_ID)
        print("[DEBUG] ☁️ Фото отправлено в архив")
    except Exception as e:
        print(f"[ERROR] Google Drive Save Error: {e}")

    await message.answer("🤖 Думаю над ответом...")

    try:
        # Генерация ответа
        data = await state.get_data()
        program = data.get("program")
        module = data.get("module")
        discipline = data.get("discipline")

        if not all([program, module, discipline]):
            await message.answer("⚠️ Не удалось определить программу, модуль и дисциплину. Пожалуйста, выбери их заново.")
            return

        answer = await generate_answer(program, module, discipline, text)
        await log_photo_request(user_id, text, answer, program, module, discipline)


        print("[DEBUG] ✅ Ответ успешно сгенерирован и залогирован")
    except Exception as e:
        print(f"[ERROR] GPT Error: {e}")
        await message.answer("⚠️ Не удалось сгенерировать ответ. Попробуй позже.")

    # 🧠 Обновим FSM-состояние (остаёмся в режиме вопросов)
    await state.set_state(ProgramSelection.asking)

    # 📊 Отображаем текущий статус, XP и количество вопросов
    xp = int(row.get("xp", 0))
    status = row.get("status", "Новичок")
    free_q = int(row.get("free_questions", 0))
    paid_q = int(row.get("paid_questions", 0))

    stats = (
        f"🧠 XP: {xp} | Статус: {status}\n"
        f"🎫 Осталось вопросов: Бесплатные — {free_q} | Платные — {paid_q}"
    )
    await message.answer(stats)
