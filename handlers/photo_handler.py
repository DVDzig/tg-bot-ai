from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from io import BytesIO
from services.vision_service import extract_text_from_image
from services.gpt_service import generate_answer  # ⬅️ GPT-функция

router = Router()

@router.message(F.photo)
async def handle_photo_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    print(f"[DEBUG] 📥 Получено фото от пользователя {user_id}")

    await message.answer("📸 Получено фото. Сейчас распознаю текст...")

    try:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        image_data = await message.bot.download_file(file.file_path)
        image_bytes = image_data.read()
        print("[DEBUG] 📷 Фото скачано")
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке фото: {e}")
        await message.answer("⚠️ Не удалось загрузить фото.")
        return

    try:
        text = extract_text_from_image(image_bytes)
        print(f"[DEBUG] 📝 Распознанный текст: {text}")
    except Exception as e:
        print(f"[ERROR] Ошибка распознавания текста: {e}")
        await message.answer("❗ Не удалось распознать текст на фото.")
        return

    if not text.strip():
        await message.answer("🔍 На фото не найден текст.")
        return

    await message.answer(f"📄 Распознанный текст:\n<pre>{text}</pre>", parse_mode="HTML")

    await message.answer("🤖 Думаю над ответом...")

    try:
        # Пока передаём фиксированные параметры
        answer = await generate_answer("Фото", "Тест", "Изображение", text)
        print(f"[DEBUG] ✅ Ответ GPT: {answer}")
        await message.answer(f"🤖 Ответ ИИ:\n\n{answer}")
    except Exception as e:
        print(f"[ERROR] GPT Error: {e}")
        await message.answer("⚠️ Не удалось сгенерировать ответ. Попробуй позже.")
