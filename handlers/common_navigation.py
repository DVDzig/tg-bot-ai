from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.admin import get_admin_menu_keyboard
from keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data.startswith("back:"))
async def handle_back_callback(call: CallbackQuery, state: FSMContext):
    target = call.data.split("back:")[1]
    await call.answer()

    if target == "main":
        await call.message.answer("🔙 Главное меню", reply_markup=get_main_menu_keyboard(call.from_user.id))

    elif target == "shop":
        from keyboards.shop import get_shop_keyboard
        await call.message.answer("🛒 Магазин", reply_markup=get_shop_keyboard())

    elif target == "program":
        await call.message.answer("Выбери программу заново:")
        await state.set_state(ProgramSelection.program)

    elif target == "module":
        await call.message.answer("Выбери модуль заново:")
        await state.set_state(ProgramSelection.module)

    elif target == "discipline":
        await call.message.answer("Выбери дисциплину заново:")
        await state.set_state(ProgramSelection.discipline)

    elif target == "level":
        await call.message.answer("Выбери уровень образования:")
        await state.set_state(ProgramSelection.level)

    elif target == "admin":
        await call.message.answer("🛠 Админ-панель", reply_markup=get_admin_menu_keyboard())

    else:
        await call.message.answer("⛔ Неизвестный пункт возврата.")
