from aiogram import Router
from aiogram.types import Message
from services.user_service import add_paid_questions

router = Router()

@router.message(lambda message: message.text.startswith("/payment_success"))
async def handle_payment_success(message: Message):
    """
    Обработка успешной оплаты от Robokassa (временное решение через команду).
    Пример команды: /payment_success 123456789 10
    Где 123456789 — user_id, 10 — количество купленных вопросов.
    """
    try:
        parts = message.text.strip().split()
        if len(parts) != 3:
            raise ValueError("Неверный формат команды")

        _, user_id, questions = parts
        user_id = int(user_id)
        questions = int(questions)

        success = add_paid_questions(user_id, questions)
        if success:
            await message.answer(
                f"✅ Успешно зачислено {questions} платных вопросов пользователю {user_id}."
            )
        else:
            await message.answer(
                f"⚠️ Пользователь с ID {user_id} не найден в таблице."
            )

    except Exception as e:
        await message.answer(
            "❌ Ошибка при обработке оплаты. Убедитесь в корректности команды."
        )
        print(f"[ERROR] Ошибка обработки оплаты: {e}")
