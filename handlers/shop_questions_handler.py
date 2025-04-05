from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.shop import get_question_packages_keyboard

router = Router()


@router.callback_query(F.data == "shop_questions")
async def show_question_packages(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "🧾 <b>Покупка вопросов</b>\n\n"
        "Ты можешь задать:\n"
        "• 1 вопрос — 10₽\n"
        "• 10 вопросов — 90₽\n"
        "• 50 вопросов — 450₽\n"
        "• 100 вопросов — 900₽\n\n"
        "После оплаты вопросы будут автоматически добавлены на твой счёт.\n"
        "Выбери нужный пакет 👇",
        reply_markup=get_question_packages_keyboard()
    )
