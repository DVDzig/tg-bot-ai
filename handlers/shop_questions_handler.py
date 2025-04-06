from aiogram import Router, F
from aiogram.types import Message
from keyboards.shop import get_question_packages_keyboard, get_shop_keyboard

router = Router()


@router.message(F.text == "💎 Вопросы")
async def shop_questions_entry_point(message: Message):
    await message.answer(
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


@router.message(F.text == "⬅️ Назад в магазин")
async def back_to_shop(message: Message):
    await message.answer("📦 Возвращаемся в магазин ⬇️", reply_markup=get_shop_keyboard())
