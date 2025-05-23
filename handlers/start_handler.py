from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states.program_states import ProgramSelection
from keyboards.main_menu import get_main_menu_keyboard
from services.referral_service import set_referrer_if_new
from services.user_service import get_or_create_user

router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start_ref(message: Message, state: FSMContext):
    await state.clear()
    
    user = message.from_user
    user_id = user.id

    # Сначала регистрируем пользователя
    await get_or_create_user(user)

    # Проверяем, передан ли реферальный параметр
    ref_param = message.text.split(" ")[1] if len(message.text.split()) > 1 else ""
    if ref_param.startswith("ref_"):
        referrer_id = ref_param.replace("ref_", "")
        await set_referrer_if_new(user_id, referrer_id)

    keyboard = get_main_menu_keyboard(user_id)
    await message.answer(
        "<b>Привет</b> 👋\n\n"
        "<b>Я — твой Образовательный консультант.</b> Помогаю разобраться в учебных дисциплинах, "
        "выбрать нужную программу и подготовиться к экзаменам вместе с ИИ.\n\n"
        "🧠 Отвечаю строго по теме — если в вопросе нет ключевых слов из выбранной дисциплины, ответа не будет.\n\n"
        "📸 Пользователи со статусом «Эксперт» и выше могут загружать фото с тестами и генерировать изображения через ИИ.\n"
        "🎯 Каждый вопрос приносит тебе XP (если нет подписки), а XP повышает твой статус и открывает бонусы, миссии и награды.\n"
        "📊 Следи за прогрессом в разделе «Мой профиль», выполняй миссии, получай достижения и бейджи.\n\n"
        "🤝 <b>Приглашай друзей и получай бонусы:</b>\n"
        "• 1 друг — +5 бесплатных вопросов\n"
        "• 3 друга — подписка <b>Лайт</b> на 3 дня\n"
        "• 10 друзей — NFT-карточка <b>Амбассадор</b>\n"
        "• 50+ друзей — подписка <b>Про</b> на 30 дней\n\n"
        "💡 Вопросы заканчиваются? Можно купить новые или оформить подписку.\n"
        "🎥 В подписке Про или Лайт ты получишь доступ к видео и другим бонусам.\n\n"
        "<b>Готов начать? Выбирай действие ⤵️</b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@router.message(CommandStart())
async def cmd_start_plain(message: Message, state: FSMContext):
    await state.clear()
    
    user = message.from_user
    user_id = user.id

    await get_or_create_user(user)

    keyboard = get_main_menu_keyboard(user_id)
    await message.answer(
        "<b>Привет</b> 👋\n\n"
        "<b>Я — твой Образовательный консультант.</b> Помогаю разобраться в учебных дисциплинах, "
        "выбрать нужную программу и подготовиться к экзаменам вместе с ИИ.\n\n"
        "🧠 Отвечаю строго по теме — если в вопросе нет ключевых слов из выбранной дисциплины, ответа не будет.\n\n"
        "📸 Пользователи со статусом «Эксперт» и выше могут загружать фото с тестами и генерировать изображения через ИИ.\n"
        "🎯 Каждый вопрос приносит тебе XP (если нет подписки), а XP повышает твой статус и открывает бонусы, миссии и награды.\n"
        "📊 Следи за прогрессом в разделе «Мой профиль», выполняй миссии, получай достижения и бейджи.\n\n"
        "🤝 <b>Приглашай друзей и получай бонусы:</b>\n"
        "• 1 друг — +5 бесплатных вопросов\n"
        "• 3 друга — подписка <b>Лайт</b> на 3 дня\n"
        "• 10 друзей — NFT-карточка <b>Амбассадор</b>\n"
        "• 50+ друзей — подписка <b>Про</b> на 30 дней\n\n"
        "💡 Вопросы заканчиваются? Можно купить новые или оформить подписку.\n"
        "🎥 В подписке Про или Лайт ты получишь доступ к видео и другим бонусам.\n\n"
        "<b>Готов начать? Выбирай действие ⤵️</b>",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )
