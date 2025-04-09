from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.context_stack import pop_step
from keyboards.main_menu import get_main_menu_keyboard
from keyboards.shop import get_shop_keyboard
from keyboards.admin import get_admin_menu_keyboard
from keyboards.info_keyboard import get_info_menu_keyboard
from keyboards.program import (
    get_level_keyboard,
    get_program_keyboard,
    get_module_keyboard,
    get_programs_by_level
)
from services.google_sheets_service import (
    get_modules_by_program,
    get_disciplines_by_module
)
from states.program_states import ProgramSelection

router = Router()


@router.message(F.text == "⬅️ Назад")
async def universal_back_handler(message: Message, state: FSMContext):
    previous = await pop_step(state)
    data = await state.get_data()

    if not previous:
        await state.clear()
        await message.answer("🔝 Главное меню", reply_markup=get_main_menu_keyboard(message.from_user.id))
        return

    if previous == "discipline":
        program = data.get("program")
        if not program:
            await state.clear()
            await message.answer("⚠️ Не удалось определить программу. Начни сначала.", reply_markup=get_main_menu_keyboard(message.from_user.id))
            return
        modules = await get_modules_by_program(program)
        await state.set_state(ProgramSelection.module)
        await message.answer("Выбери модуль:", reply_markup=get_module_keyboard(modules))

    elif previous == "module":
        level = data.get("level")
        if not level:
            await state.clear()
            await message.answer("⚠️ Уровень образования не найден. Вернись в начало.", reply_markup=get_main_menu_keyboard(message.from_user.id))
            return
        programs = get_programs_by_level(level)
        await state.set_state(ProgramSelection.program)
        await message.answer("Выбери программу:", reply_markup=get_program_keyboard(level))

    elif previous == "program":
        await state.set_state(ProgramSelection.level)
        await message.answer("Выбери уровень образования:", reply_markup=get_level_keyboard())

    elif previous == "level":
        await state.clear()
        await message.answer("🔝 Главное меню", reply_markup=get_main_menu_keyboard(message.from_user.id))

    elif previous == "shop":
        await message.answer("🛒 Магазин", reply_markup=get_shop_keyboard())

    elif previous == "admin":
        await message.answer("🛠 Админ-панель", reply_markup=get_admin_menu_keyboard())

    elif previous == "info":
        await message.answer("ℹ️ Информация", reply_markup=get_info_menu_keyboard())
    
    elif previous == "consultant":
        from keyboards.common import get_consultant_keyboard
        await state.set_state(ProgramSelection.asking)
        await message.answer("💬 Снова можешь задать вопрос ИИ:", reply_markup=get_consultant_keyboard())

    else:
        await state.clear()
        await message.answer("🔝 Главное меню", reply_markup=get_main_menu_keyboard(message.from_user.id))
