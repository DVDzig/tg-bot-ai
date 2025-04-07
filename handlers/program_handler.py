from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from config import USER_SHEET_NAME
from aiogram.fsm.context import FSMContext
from states.program_states import ProgramSelection
from services.google_sheets_service import (
    get_modules_by_program,
    get_disciplines_by_module,
    get_keywords_for_discipline,
    log_question_answer,
)
from services.sheets import (
    get_user_row_by_id, 
    update_sheet_row
) 
from services.gpt_service import generate_answer
from services.user_service import (
    get_user_row_by_id,
    increase_question_count,
    decrease_question_limit,
    add_xp_and_update_status,
    get_or_create_user
)
from keyboards.program import (
    get_level_keyboard,
    get_program_keyboard,
    get_module_keyboard,
    get_discipline_keyboard,
)
from keyboards.common import get_consultant_keyboard
from services.missions_service import check_and_apply_missions
from services.gpt_service import search_video_on_youtube
from datetime import datetime
import pytz

router = Router()


@router.message(F.text == "💬 Выбор программы")
async def start_program_selection(message: Message, state: FSMContext):
    await message.answer(
        "Выбери уровень образования:",
        reply_markup=get_level_keyboard()
    )
    await state.set_state(ProgramSelection.level)


@router.message(ProgramSelection.level)
async def select_program(message: Message, state: FSMContext):
    level = message.text
    await state.update_data(level=level)

    await message.answer(
        "Выбери программу:",
        reply_markup=get_program_keyboard(level)
    )
    await state.set_state(ProgramSelection.program)


@router.message(ProgramSelection.program)
async def select_module(message: Message, state: FSMContext):
    program = message.text.strip("📘📗📙📕📓📔 ").strip()
    await state.update_data(program=program)

    modules = await get_modules_by_program(program)
    if not modules:
        await message.answer("Не удалось найти модули для этой программы.")
        return

    await message.answer(
        "Выбери модуль:",
        reply_markup=get_module_keyboard(modules)
    )
    await state.set_state(ProgramSelection.module)


@router.message(ProgramSelection.module)
async def select_discipline(message: Message, state: FSMContext):
    module = message.text
    await state.update_data(module=module)

    data = await state.get_data()
    program = data.get("program")

    disciplines = await get_disciplines_by_module(program, module)
    if not disciplines:
        await message.answer("Не удалось найти дисциплины для этого модуля.")
        return

    await message.answer(
        "Выбери дисциплину:",
        reply_markup=get_discipline_keyboard(disciplines)
    )
    await state.set_state(ProgramSelection.discipline)


@router.message(ProgramSelection.discipline)
async def start_asking(message: Message, state: FSMContext):
    discipline = message.text
    await state.update_data(discipline=discipline)

    await message.answer(
        f"✅ Дисциплина <b>{discipline}</b> выбрана.\n\n"
        f"Теперь можешь задавать свои вопросы. Я отвечаю только по теме!",
        reply_markup=get_consultant_keyboard()
    )
    await state.set_state(ProgramSelection.asking)

@router.message(ProgramSelection.asking)
async def handle_user_question(message: Message, state: FSMContext):
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

    keywords = await get_keywords_for_discipline(program=program, module=module, discipline=discipline)

    if not any(kw.lower() in text.lower() for kw in keywords):
        await message.answer("❗ Пожалуйста, задай вопрос по теме. В нём не обнаружено ключевых слов из выбранной дисциплины.")
        return

    await message.answer("⌛ Генерирую ответ...")

    answer = await generate_answer(program=program, module=module, discipline=discipline, user_question=text)

    # Отправка видео по статусу
    status = row.get("status", "Новичок")
    videos_to_send = 0
    if status == "Профи":
        videos_to_send = 1
    elif status == "Эксперт":
        videos_to_send = 2
    elif status in ("Наставник", "Легенда", "Создатель") or plan in ("lite", "pro"):
        videos_to_send = 3

    if videos_to_send > 0:
        video_urls = await search_video_on_youtube(f"{discipline} {text}", max_results=videos_to_send)
        for video_url in video_urls:
            await message.answer_video(video_url)

    # Формируем и отправляем форматированный ответ
    header = f"📚 *Ответ по дисциплине {discipline}*:\n\n"
    stats = (
        f"🧠 Твой XP: {row.get('xp')} | Статус: {status}\n"
        f"🎫 Осталось бесплатных вопросов: {row.get('free_questions', 0)}\n"
    )
    await message.answer(f"{header}{answer}\n\n{stats}", parse_mode="Markdown")

    # Сохраняем лог вопроса и ответа
    await log_question_answer(user.id, program, discipline, text, answer)

    # Обновляем статистику пользователя
    await increase_question_count(user.id)
    if plan not in ("lite", "pro"):
        await decrease_question_limit(user.id)
    await add_xp_and_update_status(user.id)

    # Обновляем последнее взаимодействие
    updates = {
        "last_interaction": datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    }
    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

    # Награды
    rewards = await check_and_apply_missions(user.id)
    for r in rewards:
        await message.answer(r)
