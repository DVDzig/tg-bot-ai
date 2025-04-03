from aiogram import Router, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import logging
from datetime import datetime
from functools import lru_cache

from config import OPENAI_API_KEY

from handlers.start_handler import go_to_start_screen

from utils.keyboard import (
    get_programs_keyboard,
    get_modules_keyboard,
    get_disciplines_keyboard,
    get_question_keyboard,
    get_main_keyboard,
    get_levels_keyboard,
    get_bachelor_programs_keyboard,
    get_master_programs_keyboard
)

from services.gpt_service import generate_ai_response
from services.google_sheets_service import (
    get_modules,
    get_disciplines,
    log_user_activity,
    get_keywords_for_discipline,
    find_similar_questions,
    save_question_answer,
    get_all_valid_buttons
)
from services.youtube_search import search_youtube_videos
from services.qa_keywords_updater import update_keywords_from_qa
from services.user_service import (
    get_user_profile,
    get_or_create_user,
    can_ask_question,
    update_user_xp,
    determine_status,
    decrement_question_balance,
    check_and_apply_daily_challenge,
    update_user_data,
    check_thematic_challenge
)

from services.missions import get_all_missions


ALLOWED_BUTTONS = get_all_valid_buttons()

router = Router()

BACK_BUTTON = "⬅️ Назад"

# Состояния для FSM
class ProgramStates(StatesGroup):
    choosing_level = State()
    choosing_program = State()
    choosing_module = State()
    choosing_discipline = State()
    asking_question = State()
      
# Кэшируем ключевые операции для ускорения
@lru_cache(maxsize=512)
def cached_get_keywords(module, discipline):
    return get_keywords_for_discipline(module, discipline)

# Универсальный обработчик кнопки "Назад"
@router.message(lambda msg: msg.text == BACK_BUTTON)
async def universal_back_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == ProgramStates.asking_question.state:
        await state.set_state(ProgramStates.choosing_discipline)
        markup = get_disciplines_keyboard(data.get("module"))
        await message.answer("⬅️ Вернулся к выбору дисциплины:", reply_markup=markup)

    elif current_state == ProgramStates.choosing_discipline.state:
        await state.set_state(ProgramStates.choosing_module)
        markup = get_modules_keyboard(data.get("program"))
        await message.answer("⬅️ Вернулся к выбору модуля:", reply_markup=markup)

    elif current_state == ProgramStates.choosing_module.state:
        await state.set_state(ProgramStates.choosing_program)
        level = data.get("level")
        markup = get_bachelor_programs_keyboard() if level == "Бакалавриат" else get_master_programs_keyboard()
        await message.answer("⬅️ Вернулся к выбору программы:", reply_markup=markup)

    elif current_state == ProgramStates.choosing_program.state:
        await state.set_state(ProgramStates.choosing_level)
        await message.answer("⬅️ Вернулся к выбору уровня образования:", reply_markup=get_levels_keyboard())

    elif current_state == ProgramStates.choosing_level.state:
        await state.clear()
        await go_to_start_screen(message)
    else:
        await state.clear()
        await go_to_start_screen(message)

# Обработка кнопки "Начать сначала"
@router.message(lambda msg: msg.text == "🔁 Начать сначала")
async def restart_bot(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ProgramStates.choosing_level)
    await message.answer("🔁 Начнём сначала! Выбери уровень образования:", reply_markup=get_levels_keyboard())

# Обработка нажатия "Выбрать программу"
@router.message(lambda message: message.text == "🎓 Выбрать программу")
async def choose_level_handler(message: Message, state: FSMContext):
    await state.set_state(ProgramStates.choosing_level)
    await message.answer("Выбери уровень образования:", reply_markup=get_levels_keyboard())

# Обработка выбора бакалавриата или магистратуры
@router.message(ProgramStates.choosing_level)
async def level_selected(message: Message, state: FSMContext):
    level = message.text.replace("🎓 ", "")
    await state.update_data(level=level)
    await state.set_state(ProgramStates.choosing_program)

    if level == "Бакалавриат":
        await message.answer("Выбери программу бакалавриата:", reply_markup=get_bachelor_programs_keyboard())
    elif level == "Магистратура":
        await message.answer("Выбери программу магистратуры:", reply_markup=get_master_programs_keyboard())
    else:
        await message.answer("❌ Неверный выбор. Попробуй ещё раз.", reply_markup=get_levels_keyboard())

# Обработка выбранной программы
@router.message(ProgramStates.choosing_program)
async def choose_module_handler(message: Message, state: FSMContext):
    selected_program = message.text.replace("📘 ", "").replace("📗 ", "").replace("📙 ", "").replace("📕 ", "").replace("📒 ", "")
    level_data = await state.get_data()
    level = level_data.get("level")

    # Сравниваем с доступными программами по уровню
    if level == "Бакалавриат":
        valid_programs = ["МРК", "ТПР", "БХ"]
    elif level == "Магистратура":
        valid_programs = ["МСС", "ФВМ", "СА"]
    else:
        await message.answer("⚠️ Уровень не определён. Вернись назад и выбери снова.")
        return

    if selected_program not in valid_programs:
        await message.answer("⚠️ Неверный выбор программы. Используй кнопки ниже.")
        return

    await state.update_data(program=selected_program)
    modules = get_modules(selected_program)
    logging.debug(f"[DEBUG] Найдено модулей: {modules}")
    if not modules:
        await message.answer("❌ Не удалось найти модули для выбранной программы.")
        return

    await state.set_state(ProgramStates.choosing_module)
    is_admin = message.from_user.id == 150532949
    markup = get_modules_keyboard(selected_program, is_admin=is_admin)
    await message.answer("Теперь выбери модуль:", reply_markup=markup)

# Обработка выбранного модуля
@router.message(ProgramStates.choosing_module)
async def choose_discipline_handler(message: Message, state: FSMContext):
    if message.text == "🔄 Обновить ключевые слова":
        if message.from_user.id != 150532949:
            await message.answer("🚫 У тебя нет доступа к этой функции.")
            return
        await message.answer("⏳ Обновляю ключевые слова по всем дисциплинам...")
        update_keywords_from_qa()
        await message.answer("✅ Ключевые слова обновлены!")
        return

    data = await state.get_data()
    current_program = data.get("program")
    modules = get_modules(current_program)

    selected_module = message.text.replace("📗 ", "").replace("\n", " ").strip()
    normalized_modules = [m.replace("\n", " ").strip() for m in modules]
    print(f"[DEBUG] selected_module: '{selected_module}'")
    print(f"[DEBUG] normalized_modules: {normalized_modules}")
    if selected_module not in normalized_modules:
        await message.answer("⚠️ Неверный выбор модуля. Используй кнопки ниже.")
        return

    await state.update_data(module=selected_module)
    disciplines = get_disciplines(selected_module)
    if not disciplines:
        await message.answer("❌ Не удалось найти дисциплины для выбранного модуля.")
        return

    await state.set_state(ProgramStates.choosing_discipline)
    markup = get_disciplines_keyboard(selected_module)
    await message.answer("Выбери дисциплину:", reply_markup=markup)

# Обработка выбранной дисциплины
@router.message(ProgramStates.choosing_discipline)
async def choose_discipline_complete(message: Message, state: FSMContext):
    selected_discipline = message.text.replace("📕 ", "").replace("\n", " ").strip()
    data = await state.get_data()
    module = data.get("module")
    available_disciplines = get_disciplines(module)

    # Нормализуем имена дисциплин из таблицы
    normalized_disciplines = [d.replace("\n", " ").strip() for d in available_disciplines]

    if selected_discipline not in normalized_disciplines:
        await message.answer("⚠️ Неверный выбор дисциплины. Используй кнопки ниже.")
        return


    await state.update_data(discipline=selected_discipline)

    log_user_activity(
        user_id=message.from_user.id,
        plan=data.get("program"),
        module=module,
        discipline=selected_discipline
    )

    await state.set_state(ProgramStates.asking_question)
    markup = get_question_keyboard(is_admin=(message.from_user.id == 150532949))
    await message.answer(
        f"✅ Отлично! Ты выбрал дисциплину: <b>{selected_discipline}</b>\nТеперь можешь задать вопрос — я помогу!",
        parse_mode="HTML",
        reply_markup=markup
    )

# Обработка текста вопроса в состоянии asking_question
    if message.text == "🛍 Магазин":
        await state.clear()
        from handlers.start_handler import get_shop_keyboard  # импортируем тут, чтобы не было циклов
        await message.answer(
            "🛍 <b>Магазин</b>\n\n"
            "Выбери, что хочешь купить:\n"
            "💬 Вопросы — для продолжения общения с ИИ\n"
            "💳 Подписка — чтобы снять лимиты и открыть бонусы\n\n"
            "👇 Выбери категорию ниже:",
            parse_mode="HTML",
            reply_markup=get_shop_keyboard()
        )
        return

    if message.text == "👤 Мой профиль":
        await state.clear()
        profile = get_user_profile(message.from_user.id)
        await message.answer(
            f"👤 <b>Твой профиль</b>:\n"
            f"Имя: {profile['first_name'] or '@' + profile['username']}"
            f"Статус: {profile['status']}\n"
            f"XP: {profile['xp']}\n"
            f"Бесплатные вопросы: {profile['free_questions']}\n"
            f"Платные вопросы: {profile['paid_questions']}",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )
        return

    if message.text in ["📊 Лидерборд", "🔁 Начать сначала"]:
        return

    logging.debug(f"[DEBUG] Вошли в состояние задавания вопроса. Сообщение: {message.text}")

    user_id = message.from_user.id
    if not can_ask_question(user_id):
        user_data = get_user_profile(user_id)
        premium = user_data.get("premium_status", "none")

        text = "❌ У тебя закончились вопросы!\n\n"

        if premium == "none":
            text += (
                "🔓 <b>Хочешь продолжить без ограничений?</b>\n\n"
                "• <b>Лайт</b> — безлимит на 7 дней\n"
                "• <b>Про</b> — видео и приоритет от ИИ\n\n"
                "Нажми «Купить доступ» ниже ⬇️"
            )
        else:
            text += "Ты можешь купить дополнительные, чтобы продолжить 🤖"

        await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())
        await state.clear()
        return

    data = await state.get_data()

    discipline = data.get("discipline")
    program = data.get("program")
    module = data.get("module")
    question = message.text

    keywords = cached_get_keywords(module, discipline)
    print(f"[DEBUG] Keywords: {keywords}")
    print(f"[DEBUG] User question: {question}")
    history = find_similar_questions(discipline, keywords or "")

    if not keywords or not any(kw.strip().lower() in question.lower() for kw in keywords.split(",") if kw.strip()):
        await message.answer(
            "❌ Похоже, твой вопрос не относится к выбранной дисциплине. "
            "Попробуй переформулировать или используй ключевые слова по теме.",
            reply_markup=get_question_keyboard(is_admin=(user_id == 150532949))
        )
        return

    if not decrement_question_balance(user_id):
        await state.clear()
        await message.answer("❌ У тебя закончились вопросы!\n")
        await go_to_start_screen(message)
        return

    ai_response = generate_ai_response(question, keywords, history)

    save_question_answer(user_id, program, module, discipline, question, ai_response)

    new_xp, new_status = update_user_xp(user_id)
    profile = get_user_profile(user_id)
    
    premium = profile.get("premium_status", "none")
    last_prompt = profile.get("last_upgrade_prompt", "")
    today = datetime.now().strftime("%Y-%m-%d")

    if premium == "none" and new_xp >= 50 and last_prompt != today:
        await message.answer(
            "🔥 Ты задал уже больше 50 вопросов — круто! 💪\n\n"
            "Хочешь ещё больше?\n"
            "💡 <b>Лайт</b> — безлимит на 7 дней\n"
            "🚀 <b>Про</b> — приоритет, видео и +100 вопросов\n\n"
            "Доступно в разделе <b>«Купить доступ»</b> 👇",
            parse_mode="HTML"
        )
        update_user_data(user_id, {"last_upgrade_prompt": today})
    
    free_q = profile["free_questions"]

    # Заменяем кэшированный профиль на актуальный
    profile = get_user_profile(user_id)
    free_q = profile["free_questions"]
    status = profile["status"]

    # Новый статус и прогресс
    status, _ = determine_status(new_xp)
    thresholds = {
        "новичок": (0, 10),
        "опытный": (11, 50),
        "профи": (51, 100),
        "эксперт": (101, 150)
    }
    min_xp, max_xp = thresholds.get(status, (0, 10))
    progress = int(((new_xp - min_xp) / (max_xp - min_xp)) * 100) if max_xp > min_xp else 100
    progress_bar = "🟩" * min(5, int(progress / 1)) + "⬜️" * (5 - min(5, int(progress / 1)))

    reply = (
        f"📚 <b>Ответ по дисциплине</b> <i>{discipline}</i>:\n\n"
        f"{ai_response}\n\n"
        f"🎯 Твой XP: {new_xp} | Статус: {status} (прогресс: {progress_bar} {progress}%)\n"
        f"🆓 Осталось бесплатных вопросов: {free_q}"
    )

    # ✅ Проверка всех миссий
    completed_missions = []
    for mission in get_all_missions():
        try:
            if mission.check(user_id):
                completed_missions.append(f"🎯 {mission.title} +{mission.reward} XP")
        except Exception as e:
            print(f"[Mission Error] {mission.id}: {e}")

    if completed_missions:
        reply += "\n\n" + "\n".join(completed_missions)

    # 🎯 Миссия: 3 дисциплины за день
    if check_thematic_challenge(user_id):
        reply += "\n\n📚 Выполнена миссия: 3 дисциплины за день! +5 XP"

    # Ежедневный челлендж
    if check_and_apply_daily_challenge(user_id):
        reply += "\n\n🏆 Ты выполнил ежедневный челлендж и получил +2 XP!"

        if profile.get("premium_status", "none") == "none":
            last_prompt = profile.get("last_upgrade_prompt", "")
            today = datetime.now().strftime("%Y-%m-%d")

            if last_prompt != today:
                await message.answer(
                    "🔥 Челлендж пройден — супер!\n\n"
                    "Готов двигаться быстрее и глубже? 📚\n"
                    "💡 <b>Лайт</b> — безлимит на 7 дней\n"
                    "🚀 <b>Про</b> — приоритет, видео и +100 вопросов\n\n"
                    "Доступно в разделе <b>«Купить доступ»</b>",
                    parse_mode="HTML"
                )
                update_user_data(user_id, {"last_upgrade_prompt": today})

    # Рекомендованные видео
    if status in ["профи", "эксперт"]:
        count = 3 if status == "эксперт" else 1
        videos = search_youtube_videos(question, max_results=count)
        if videos:
            reply += "\n\n🎥 <b>Рекомендуемые видео:</b>\n"
            for link in videos:
                reply += f"{link}\n"

    # Проверка, админ ли пользователь (нужно для reply_markup)
    is_admin = user_id == 150532949

    await message.answer(reply, parse_mode="HTML", reply_markup=get_question_keyboard(is_admin=is_admin))

# Запрет писать в чат с ботом вне общения с ИИ
@router.message(lambda msg: msg.text not in ALLOWED_BUTTONS)
async def block_input(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != ProgramStates.asking_question.state:
        await message.delete()
        await message.answer("❗Используй кнопки для навигации.")

