from aiogram import Router, F
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InputMediaVideo,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from states.program_states import ProgramSelection
from services.google_sheets_service import (
    get_modules_by_program, 
    get_disciplines_by_module,
    get_keywords_for_discipline, 
    log_question_answer
)
from services.gpt_service import generate_answer
from services.user_service import (
    get_user_row_by_id, 
    increase_question_count, 
    decrease_question_limit,
    increase_question_count,
    decrease_question_limit,
    add_xp_and_update_status
)
   
from services.missions_service import check_and_apply_missions
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.utils import get_back_keyboard
from services.gpt_service import search_video_on_youtube

router = Router()

@router.message(F.text == "💬 Выбор программы")
async def start_program_selection(message: Message, state: FSMContext):
    await state.clear()
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎓 Бакалавриат")],
            [KeyboardButton(text="🎓 Магистратура")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери уровень образования:", reply_markup=kb)
    await state.set_state(ProgramSelection.level)

@router.message(ProgramSelection.level)
async def select_program(message: Message, state: FSMContext):
    level = message.text
    await state.update_data(level=level)

    if "Бакалавриат" in level:
        programs = ["📘 МРК", "📗 ТПР", "📙 БХ"]
    elif "Магистратура" in level:
        programs = ["📕 МСС", "📓 СА", "📔 ФВМ"]
    else:
        await message.answer("Выбери из предложенных вариантов.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=p)] for p in programs],
        resize_keyboard=True
    )
    await message.answer("Выбери программу:", reply_markup=kb)
    await message.answer("⬅️ Назад:", reply_markup=get_back_keyboard("level"))
    await state.set_state(ProgramSelection.program)

@router.message(ProgramSelection.program)
async def select_module(message: Message, state: FSMContext):
    program = message.text.replace("📘 ", "").replace("📗 ", "").replace("📙 ", "").replace("📕 ", "").replace("📒 ", "").replace("📓 ", "").replace("📔 ", "")
    await state.update_data(program=program)

    modules = await get_modules_by_program(program)
    if not modules:
        await message.answer("Не удалось найти модули для этой программы.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=mod)] for mod in modules],
        resize_keyboard=True
    )
    await message.answer("Выбери модуль:", reply_markup=kb)
    await message.answer("⬅️ Назад:", reply_markup=get_back_keyboard("program"))
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

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=disc)] for disc in disciplines],
        resize_keyboard=True
    )
    await message.answer("Выбери дисциплину:", reply_markup=kb)
    await message.answer("⬅️ Назад:", reply_markup=get_back_keyboard("module"))
    await state.set_state(ProgramSelection.discipline)

@router.message(ProgramSelection.discipline)
async def start_asking(message: Message, state: FSMContext):
    discipline = message.text
    await state.update_data(discipline=discipline)

    await message.answer(
        f"✅ Дисциплина <b>{discipline}</b> выбрана.\n\n"
        f"Теперь можешь задавать свои вопросы. Я отвечаю только по теме!",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ProgramSelection.asking)

@router.message(ProgramSelection.asking)
async def handle_user_question(message: Message, state: FSMContext):
    user = message.from_user
    text = message.text.strip()
    data = await state.get_data()

    # Получаем данные пользователя
    row = await get_user_row_by_id(user.id)
    if not row:
        await message.answer("Ошибка: не удалось получить данные пользователя.")
        return

    # Проверка подписки / лимитов
    plan = row.get("plan")
    free_q = int(row.get("free_questions", 0))
    paid_q = int(row.get("paid_questions", 0))
    if plan not in ("lite", "pro") and free_q + paid_q <= 0:
        await message.answer("У тебя закончились вопросы. Купи пакет в разделе 🛒 Магазин.")
        return

    # Получаем ключевые слова дисциплины
    keywords = await get_keywords_for_discipline(
        program=data.get("program"),
        module=data.get("module"),
        discipline=data.get("discipline")
    )

    # Проверка на наличие ключевых слов в вопросе
    if not any(kw.lower() in text.lower() for kw in keywords):
        await message.answer("❗ Пожалуйста, задай вопрос по теме. В нём не обнаружено ключевых слов из выбранной дисциплины.")
    
    is_valid = any(kw.lower() in text.lower() for kw in keywords)    
    if is_valid:
        await log_question_answer(user.id, data.get("program"), data.get("discipline"), text, answer)
        await increase_question_count(user.id)
        await decrease_question_limit(user.id)
        await add_xp_and_update_status(user.id)
        return

    # Генерация ответа
    answer = await generate_answer(
        program=data.get("program"),
        module=data.get("module"),
        discipline=data.get("discipline"),
        user_question=text
    )

    # Получаем статус пользователя и количество видео
    status = row.get("status", "Новичок")
    videos_to_send = 0

    # Определяем количество видео по статусу
    if status == "Профи":
        videos_to_send = 1
    elif status == "Эксперт":
        videos_to_send = 2
    elif status in ("Наставник", "Легенда", "Создатель"):
        videos_to_send = 3
    elif plan in ("lite", "pro"):
        videos_to_send = 3  # Лайт и Про всегда 3 видео

    # Поиск видео через YouTube API
    if videos_to_send > 0:
        video_urls = await search_video_on_youtube(f"{data['discipline']} {text}", max_results=videos_to_send)
        for video_url in video_urls:
            await message.answer_video(video_url)

    # Отправляем текстовый ответ
    await message.answer(answer)

    # Логирование
    await log_question_answer(user.id, data.get("program"), data.get("discipline"), text, answer)

    # Обновление счётчиков
    await increase_question_count(user.id)
    if plan not in ("lite", "pro"):
        await decrease_question_limit(user.id)

    # Проверка миссий
    rewards = await check_and_apply_missions(user.id)
    for r in rewards:
        await message.answer(r)

    await message.answer("⬅️ Назад:", reply_markup=get_back_keyboard("context"))
