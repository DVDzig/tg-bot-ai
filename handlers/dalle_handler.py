from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from services.google_sheets_service import log_image_request
from services.user_service import update_user_after_answer, decrease_question_limit
from states.program_states import ProgramSelection

router = Router()

@router.message(ProgramSelection.asking, F.text == "🎨 Сгенерировать изображение")
async def prompt_dalle(message: Message, state: FSMContext):
    await state.set_state(ProgramSelection.waiting_for_dalle_prompt)
    await message.answer("🎨 Напиши, что нужно сгенерировать:")

@router.message(ProgramSelection.waiting_for_dalle_prompt)
async def dalle_generate(message: Message, state: FSMContext):
    user_id = message.from_user.id
    prompt = message.text

    success = await decrease_question_limit(user_id)
    if not success:
        await message.answer("❌ У вас закончились вопросы. Пополните лимит в разделе 🛒 Магазин.")
        await state.set_state(ProgramSelection.asking)
        return

    await message.answer("🎨 Генерирую изображение через DALL·E...")

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        image_url = response.data[0].url
        await message.answer_photo(photo=image_url, caption="Готово! ✨")

        await update_user_after_answer(user_id, bot=message.bot)
        await log_image_request(user_id, prompt, "успешно")

    except Exception as e:
        print(f"[DALLE ERROR] {e}")
        await message.answer("⚠️ Ошибка генерации. Попробуй другой запрос.")
        await log_image_request(user_id, prompt, "ошибка")

    finally:
        await state.set_state(ProgramSelection.asking)