from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states.program_states import ProgramSelection
from keyboards.program import (
    get_level_keyboard,
    get_program_keyboard,
    get_module_keyboard,
    get_discipline_keyboard,
)
from keyboards.common import get_consultant_keyboard
from services.google_sheets_service import (
    get_modules_by_program,
    get_disciplines_by_module,
    get_keywords_for_discipline,
    log_question_answer,
    log_image_request
)
from services.user_service import get_user_row_by_id, update_user_after_answer
from services.gpt_service import generate_answer, search_video_on_youtube
from services.missions_service import check_and_apply_missions
from services.sheets import update_sheet_row
from datetime import datetime
import pytz
from keyboards.shop import get_shop_keyboard
from config import VIDEO_URLS, OPENAI_API_KEY
import re
from openai import AsyncOpenAI

router = Router()

@router.message(F.text == "💬 Выбор программы")
async def start_program_selection(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ProgramSelection.level)
    await message.answer("Выбери уровень образования:", reply_markup=get_level_keyboard())

@router.message(ProgramSelection.level)
async def select_program(message: Message, state: FSMContext):
    if message.text not in ["🎓 Бакалавриат", "🎓 Магистратура"]:
        return
    level = message.text
    await state.update_data(level=level)
    await state.set_state(ProgramSelection.program)
    await message.answer("Выбери программу:", reply_markup=get_program_keyboard(level))

@router.message(ProgramSelection.program)
async def select_module(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад в уровень образования":
        await state.clear()
        await state.set_state(ProgramSelection.level)
        await message.answer("Выбери уровень образования:", reply_markup=get_level_keyboard())
        return

    known_programs = ["📘 МРК", "📗 ТПР", "📙 БХ", "📕 МСС", "📓 СА", "📔 ФВМ"]
    if message.text not in known_programs:
        return

    program = message.text.strip("📘📗📙📕📓📔 ").strip()
    await state.update_data(program=program)
    modules = await get_modules_by_program(program)
    if not modules:
        await message.answer("Не удалось найти модули для этой программы.")
        return
    await state.set_state(ProgramSelection.module)
    await message.answer("Выбери модуль:", reply_markup=get_module_keyboard(modules))

@router.message(ProgramSelection.module)
async def select_discipline(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад в программы":
        data = await state.get_data()
        level = data.get("level")
        await state.set_state(ProgramSelection.program)
        await message.answer("Выбери программу:", reply_markup=get_program_keyboard(level))
        return

    module = message.text.replace("🧩", "").strip()  # ✅ очистка иконки
    await state.update_data(module=module)
    data = await state.get_data()
    program = data.get("program")
    disciplines = await get_disciplines_by_module(program, module)
    if not disciplines:
        await message.answer("Не удалось найти дисциплины для этого модуля.")
        return
    await state.set_state(ProgramSelection.discipline)
    await message.answer("Выбери дисциплину:", reply_markup=get_discipline_keyboard(disciplines))

@router.message(ProgramSelection.discipline)
async def select_asking(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад в модули":
        data = await state.get_data()
        program = data.get("program")
        modules = await get_modules_by_program(program)
        await state.set_state(ProgramSelection.module)
        await message.answer("Выбери модуль:", reply_markup=get_module_keyboard(modules))
        return

    discipline = message.text.replace("🧠", "").strip()
    await state.update_data(discipline=discipline)
    await state.set_state(ProgramSelection.asking)
    status = row.get("status", "").split()[-1]  # получаем текущий статус
    await message.answer(
        f"✅ Дисциплина <b>{discipline}</b> выбрана.\n\nТеперь можешь задавать свои вопросы. Я отвечаю только по теме!",
        reply_markup=get_consultant_keyboard(user_status=status)
    )


@router.message(ProgramSelection.asking)
async def handle_question(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад в дисциплины":
        data = await state.get_data()
        program = data.get("program")
        module = data.get("module")
        disciplines = await get_disciplines_by_module(program, module)
        await state.set_state(ProgramSelection.discipline)
        await message.answer("Выбери дисциплину:", reply_markup=get_discipline_keyboard(disciplines))
        return
    
    if message.text == "🛒 Магазин":
        await message.answer("🛒 Магазин", reply_markup=get_shop_keyboard())
        return
    
    user = message.from_user
    text = message.text.strip()
    data = await state.get_data()
    row = await get_user_row_by_id(user.id)

    if not row:
        await message.answer("Ошибка: не удалось получить данные пользователя.")
        return

    plan = row.get("plan")
    free_q = int(row.get("free_questions", 0))
    paid_q = int(row.get("paid_questions", 0))

    if plan not in ("lite", "pro") and free_q + paid_q <= 0:
        await message.answer("У тебя закончились вопросы. Купи пакет в разделе 🛒 Магазин.")
        return

    program = data.get("program")
    module = data.get("module")
    discipline = data.get("discipline")

    if not all([program, module, discipline]):
        await message.answer("⚠️ Ошибка: данные дисциплины не найдены. Пожалуйста, выбери программу заново.")
        await state.clear()
        return

    try:
        keywords = await get_keywords_for_discipline(program, module, discipline)
    except Exception as e:
        print(f"[KEYWORDS ERROR] {e}")
        await message.answer("⚠️ Не удалось загрузить ключевые слова. Попробуй выбрать дисциплину заново.")
        await state.clear()
        return

    if not keywords or not any(kw.lower() in text.lower() for kw in keywords):
        await message.answer("❗ Пожалуйста, задай вопрос по теме. В нём не обнаружено ключевых слов из выбранной дисциплины.")
        return

    await message.answer("⌛ Генерирую ответ...")

    try:
        answer = await generate_answer(program, module, discipline, text)
    except Exception as e:
        print(f"[GPT ERROR] {e}")
        await message.answer("⚠️ Ошибка генерации ответа. Попробуй переформулировать вопрос позже.")
        return

    if not answer:
        await message.answer("⚠️ ИИ не смог сгенерировать ответ. Попробуй задать вопрос по-другому.")
        return


    # Очистка эмодзи и пробелов
    status = re.sub(r"[^\w\s]", "", row.get("status", "Новичок")).strip()
    plan = row.get("plan", "").strip().lower()

    videos_to_send = VIDEO_URLS.get(status, 0)
    if plan in VIDEO_URLS:
        videos_to_send = max(videos_to_send, VIDEO_URLS[plan])

    if videos_to_send > 0:
        try:
            video_urls = await search_video_on_youtube(f"{discipline} {text}", max_results=videos_to_send)
            for url in video_urls:
                if url.strip():
                    try:
                        await message.answer(f"🎬 Видео по теме:\n{url}")
                        await asyncio.sleep(1.5)  # ⏳ если отправляется несколько
                    except Exception as e:
                        print(f"[VIDEO ERROR] {e}")
                else:
                    print("[VIDEO WARNING] Пустая ссылка пропущена")

        except Exception as e:
            print(f"[VIDEO ERROR] {e}")

    header = f"📚 *Ответ по дисциплине {discipline}*:\n\n"
    stats = (
        f"🧠 Твой XP: {row.get('xp')} | Статус: {status}\n"
        f"🎁 Осталось: 🎫 {row.get('free_questions', 0)} | 💰 {row.get('paid_questions', 0)}"
    )


    try:
        await message.answer(f"{header}{answer}\n\n{stats}", parse_mode="Markdown")
    except Exception as e:
        print(f"[MESSAGE ERROR] {e}")
        await message.answer("⚠️ Ответ слишком длинный или произошла ошибка при отправке.")

    await log_question_answer(user.id, program, discipline, text, answer)
    await update_user_after_answer(message.from_user.id, bot=message.bot)

    updates = {
        "last_interaction": datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    }
    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

    rewards = await check_and_apply_missions(user.id)
    for r in rewards:
        await message.answer(r)

@router.message(ProgramSelection.asking, F.text == "🎨 Сгенерировать изображение")
async def prompt_dalle(message: Message, state: FSMContext):
    await state.set_state(ProgramSelection.waiting_for_dalle_prompt)
    await message.answer("🎨 Напиши, что нужно сгенерировать:")

@router.message(ProgramSelection.waiting_for_dalle_prompt)
async def dalle_generate(message: Message, state: FSMContext):
    user_id = message.from_user.id
    prompt = message.text

    # 1️⃣ Пробуем списать вопрос сначала
    success = await decrease_question_limit(user_id)
    if not success:
        await message.answer("❌ У вас закончились вопросы. Пополните лимит в разделе 🛒 Магазин.")
        await state.set_state(ProgramSelection.asking)
        return

    await message.answer("🎨 Генерирую изображение через DALL·E...")

    try:
        # 2️⃣ Генерация изображения
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

        # 3️⃣ Обновляем XP и статус
        await update_user_after_answer(user_id, bot=message.bot)

        # 4️⃣ Логируем успешный запрос
        await log_image_request(user_id, prompt, "успешно")

    except Exception as e:
        print(f"[DALLE ERROR] {e}")
        await message.answer("⚠️ Ошибка генерации. Попробуй другой запрос.")

        # ❌ Логируем неудачный запрос
        await log_image_request(user_id, prompt, "ошибка")

    await state.set_state(ProgramSelection.asking)
