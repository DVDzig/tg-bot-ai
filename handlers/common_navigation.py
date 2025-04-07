from aiogram.types import Message
from states.program_states import ProgramSelection
from keyboards.program import (
    get_level_keyboard,
    get_program_keyboard,
    get_module_keyboard,
    get_discipline_keyboard
)
from keyboards.main_menu import get_main_menu_keyboard
from services.google_sheets_service import (
    get_modules_by_program,
    get_disciplines_by_module
)
from aiogram.fsm.context import FSMContext

from aiogram import Router, F
router = Router()

@router.message(F.text == "⬅️ Назад")
async def handle_text_back(message: Message, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()

    print(f"[⬅️ Назад] user_id={message.from_user.id}, state={current_state}")

    if current_state == ProgramSelection.asking:
        disciplines = await get_disciplines_by_module(data["program"], data["module"])
        await state.set_state(ProgramSelection.discipline)
        await message.answer("Выбери дисциплину:", reply_markup=get_discipline_keyboard(disciplines))

    elif current_state == ProgramSelection.discipline:
        modules = await get_modules_by_program(data["program"])
        await state.set_state(ProgramSelection.module)
        await message.answer("Выбери модуль:", reply_markup=get_module_keyboard(modules))

    elif current_state == ProgramSelection.module:
        level = data.get("level")
        await state.set_state(ProgramSelection.program)
        await message.answer("Выбери программу:", reply_markup=get_program_keyboard(level))

    elif current_state == ProgramSelection.program:
        await state.set_state(ProgramSelection.level)
        await message.answer("Выбери уровень образования:", reply_markup=get_level_keyboard())

    else:
        # Лучше явно сказать, что пользователь уже в главном меню
        await state.clear()
        await message.answer("Ты уже находишься в главном меню.", reply_markup=get_main_menu_keyboard(message.from_user.id))
