from aiogram import Router, F
from aiogram.types import Message
from services.user_service import (
    get_user_row_by_id, 
    update_user_after_answer, 
    decrease_question_limit
)
from services.gpt_service import generate_answer
import io
from services.vision_service import extract_text_from_image
from services.google_sheets_service import log_photo_request


router = Router()

@router.message(F.photo)
async def handle_photo_with_test(message: Message):
    user_id = message.from_user.id
    row = await get_user_row_by_id(user_id)
    if not row:
        await message.answer("Ошибка: не удалось получить данные пользователя.")
        return

    plan = row.get("plan", "").lower()
    status = row.get("status", "")
    status_clean = status.split()[-1]

    if plan != "pro" and status_clean not in ["Эксперт", "Наставник", "Легенда", "Создатель"]:
        await message.answer("🛑 Эта функция доступна только для пользователей со статусом Эксперт+ или подпиской Про.")
        return

    # 1️⃣ Списываем вопрос
    success = await decrease_question_limit(user_id)
    if not success:
        await message.answer("❌ У вас закончились вопросы. Пополните лимит в разделе 🛒 Магазин.")
        return

    await message.answer("📸 Фото получено. Распознаю текст через Google Vision...")

    photo = message.photo[-1]
    photo_bytes = await photo.download(destination=io.BytesIO())
    photo_bytes.seek(0)
    image_data = photo_bytes.read()

    text = extract_text_from_image(image_data)

    if not text.strip():
        await message.answer("❗ Не удалось распознать текст. Проверь, что на фото есть чёткий текст.")
        return

    await message.answer(f"📄 Распознанный текст:\n<pre>{text}</pre>", parse_mode="HTML")

    try:
        answer = await generate_answer("Общий анализ", "Тест", "Фотозапрос", text)
        await message.answer(f"🤖 Ответ ИИ:\n\n{answer}")

        # 2️⃣ Обновляем XP, статус и миссии
        await update_user_after_answer(user_id, bot=message.bot)

        # 3️⃣ Логируем
        await log_photo_request(user_id, text, answer)

    except Exception as e:
        print(f"[GPT ERROR] {e}")
        await message.answer("⚠️ Не удалось сгенерировать ответ. Попробуй позже.")
