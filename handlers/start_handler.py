from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from keyboards.main_menu import get_main_menu_keyboard
from aiogram.fsm.context import FSMContext
from states.program_states import ProgramSelection


router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ProgramSelection.level)  # Устанавливаем начальное состояние
    user_id = message.from_user.id
    keyboard = get_main_menu_keyboard(user_id)
    await message.answer(
        "<b>Привет</b> 👋\n\n"
        "<b>Я — твой Образовательный консультант.</b> Помогаю разобраться в учебных дисциплинах, "
        "выбрать нужную программу и подготовиться к экзаменам вместе с ИИ.\n\n"
        "🧠 Отвечаю строго по теме — если в вопросе нет ключевых слов из выбранной дисциплины, ответа не будет.\n\n"
        "📸 Пользователи со статусом «Эксперт» и выше могут загружать фото с тестами и генерировать изображения через ИИ.\n"
        "🎯 Каждый вопрос приносит тебе XP (если нет подписки), а XP повышает твой статус и открывает бонусы, миссии и награды.\n"
        "📊 Следи за прогрессом в разделе «Мой профиль», выполняй миссии, получай достижения и бейджи.\n\n"
        "💡 Вопросы заканчиваются? Можно купить новые или оформить подписку.\n"
        "🎥 В подписке Про или Лайт ты получишь доступ к видео и другим бонусам.\n\n"
        "<b>Готов начать? Выбирай действие ⤵️</b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
