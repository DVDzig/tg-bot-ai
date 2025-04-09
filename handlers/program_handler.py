from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from states.program_states import ProgramSelection
from services.google_sheets_service import (
    get_modules_by_program,
    get_disciplines_by_module,
    get_keywords_for_discipline,
    log_question_answer,
)
from services.sheets import get_user_row_by_id, update_sheet_row
from services.gpt_service import generate_answer, search_video_on_youtube
from services.user_service import get_user_row_by_id, update_user_after_answer
from services.missions_service import check_and_apply_missions
from keyboards.program import (
    get_level_keyboard,
    get_program_keyboard,
    get_module_keyboard,
    get_discipline_keyboard,
)
from keyboards.common import get_consultant_keyboard
from keyboards.shop import get_shop_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from datetime import datetime
import pytz

router = Router()

# Старт
@router.message(F.text == "💬 Выбор программы")
async def start_program_selection(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ProgramSelection.level)
    await message.answer("Выбери уровень образования:", reply_markup=get_level_keyboard())

@router.message(ProgramSelection.level)
async def select_program(message: Message, state: FSMContext):
    print("➡️ Выбран уровень:", message.text)
    if message.text not in ["🎓 Бакалавриат", "🎓 Магистратура"]:
        return
    level = message.text
    await state.update_data(level=level)
    await state.set_state(ProgramSelection.program)
    await message.answer("Выбери программу:", reply_markup=get_program_keyboard(level))

@router.message(ProgramSelection.program)
async def select_module(message: Message, state: FSMContext):
    if message.text.startswith("⬅️"):
        print("❗ select_module — перехватил кнопку назад:", message.text)
        return

    known_programs = ["📘 МРК", "📗 ТПР", "📙 БХ", "📕 МСС", "📓 СА", "📔 ФВМ"]
    if message.text not in known_programs:
        print("❌ Неизвестная программа:", message.text)
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
    if message.text.startswith("⬅️"):
        return
    module = message.text
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
async def start_asking(message: Message, state: FSMContext):
    if message.text.startswith("⬅️"):
        return
    discipline = message.text
    await state.update_data(discipline=discipline)
    await state.set_state(ProgramSelection.asking)
    await message.answer(
        f"✅ Дисциплина <b>{discipline}</b> выбрана.\n\nТеперь можешь задавать свои вопросы. Я отвечаю только по теме!",
        reply_markup=get_consultant_keyboard()
    )

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

    status = row.get("status", "Новичок")
    videos_to_send = 0
    if status == "Профи":
        videos_to_send = 1
    elif status == "Эксперт":
        videos_to_send = 2
    elif status in ("Наставник", "Легенда", "Создатель") or plan in ("lite", "pro"):
        videos_to_send = 3

    if videos_to_send > 0:
        try:
            video_urls = await search_video_on_youtube(f"{discipline} {text}", max_results=videos_to_send)
            for video_url in video_urls:
                await message.answer_video(video_url)
        except Exception as e:
            print(f"[VIDEO ERROR] {e}")

    header = f"📚 *Ответ по дисциплине {discipline}*:\n\n"
    stats = (
        f"🧠 Твой XP: {row.get('xp')} | Статус: {status}\n"
        f"🎫 Осталось бесплатных вопросов: {row.get('free_questions', 0)}\n"
    )

    try:
        await message.answer(f"{header}{answer}\n\n{stats}", parse_mode="Markdown")
    except Exception as e:
        print(f"[MESSAGE ERROR] {e}")
        await message.answer("⚠️ Ответ слишком длинный или произошла ошибка при отправке.")

    await log_question_answer(user.id, program, discipline, text, answer)
    await update_user_after_answer(user.id)
    updates = {
        "last_interaction": datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S")
    }
    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

    rewards = await check_and_apply_missions(user.id)
    for r in rewards:
        await message.answer(r)

# 🔙 Назад — отладочные хендлеры
@router.message(F.text == "⬅️ Назад в дисциплины")
async def back_to_discipline(message: Message, state: FSMContext):
    print("⬅️ Назад в дисциплины →", await state.get_state())
    data = await state.get_data()
    await state.update_data(discipline=None)
    disciplines = await get_disciplines_by_module(data.get("program"), data.get("module"))
    await state.set_state(ProgramSelection.discipline)
    await message.answer("Выбери дисциплину:", reply_markup=get_discipline_keyboard(disciplines))

@router.message(F.text == "⬅️ Назад в модули")
async def back_to_module(message: Message, state: FSMContext):
    print("⬅️ Назад в модули →", await state.get_state())
    data = await state.get_data()
    await state.update_data(module=None, discipline=None)
    modules = await get_modules_by_program(data.get("program"))
    await state.set_state(ProgramSelection.module)
    await message.answer("Выбери модуль:", reply_markup=get_module_keyboard(modules))

@router.message(F.text == "⬅️ Назад в программы")
async def back_to_program(message: Message, state: FSMContext):
    print("⬅️ Назад в программы →", await state.get_state())
    data = await state.get_data()
    await state.update_data(program=None, module=None)
    level = data.get("level")
    await state.set_state(ProgramSelection.program)
    await message.answer("Выбери программу:", reply_markup=get_program_keyboard(level))

@router.message(F.text == "⬅️ Назад в уровень образования")
async def back_to_level(message: Message, state: FSMContext):
    print("⬅️ Назад в уровень образования →", await state.get_state())
    await state.clear()
    await state.set_state(ProgramSelection.level)
    await message.answer("Выбери уровень образования:", reply_markup=get_level_keyboard())

@router.message(F.text == "⬅️ Назад в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    print("⬅️ Назад в главное меню →", await state.get_state())
    await state.clear()
    await message.answer("🔝 Главное меню", reply_markup=get_main_menu_keyboard(message.from_user.id))
