from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from keyboards.info_keyboard import get_info_menu_keyboard
from texts.help_text import HELP_TEXT
from texts.statuses_text import STATUS_TEXT
from texts.subscriptions_text import SUBSCRIPTIONS_TEXT

router = Router()

@router.message(F.text == "ℹ️ Info")
async def log_wrapper(message: Message):
    print(f'🧪 Нажата кнопка: {message.text}')
    return await real_ℹ️ Info_handler(message)
async def show_info_menu(message: Message):
    await message.answer("ℹ️ Выбери, что тебе интересно:", reply_markup=get_info_menu_keyboard())


@router.callback_query(F.data == "info_help")
async def show_help_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer(HELP_TEXT)


@router.callback_query(F.data == "info_statuses")
async def show_statuses_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer(STATUS_TEXT)


@router.callback_query(F.data == "info_subscriptions")
async def show_subscriptions_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer(SUBSCRIPTIONS_TEXT)

@router.callback_query(F.data == "info_statuses")
async def show_statuses(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "🎖️ <b>Статусы</b>\n\n"
        "🟢 Новичок — 0–9 XP\n"
        "🔸 Опытный — 10–49 XP\n"
        "🚀 Профи — 50–149 XP (1 видео по теме)\n"
        "👑 Эксперт — 150–299 XP (2 видео + генерация изображений DALL·E)\n"
        "🧠 Наставник — 300–999 XP (3 видео + генерация изображений)\n"
        "🔥 Легенда — 1000–4999 XP (3 видео + генерация изображений + приоритет на ответы)\n"
        "👑 Создатель — 5000+ XP (все функции, безлимит, админ-доступ)"
    )


@router.callback_query(F.data == "info_subscriptions")
async def show_subscriptions(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "💳 <b>Подписки</b>\n\n"
        "🔓 <b>Лайт</b> — безлимит на 7 дней.\n"
        "📌 В течение недели ты можешь задавать сколько угодно вопросов, не тратя бесплатные или платные. "
        "Идеально, если хочешь активно заниматься, но пока не готов на Про.\n"
        "⚠️ XP в этот период не начисляется.\n\n"

        "🔓 <b>Про</b> — максимум возможностей!\n"
        "• Безлимитные вопросы\n"
        "• +100 платных вопросов в подарок\n"
        "• Доступ к видео по теме (до 3)\n"
        "• Приоритетные ответы\n"
        "• Генерация изображений через DALL·E (визуальные подсказки!)\n\n"
        "🛒 Подписки можно оформить в разделе «Магазин»"
    )


@router.callback_query(F.data == "info_help")
async def show_help(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "❓ <b>Как использовать?</b>\n"
        "1. Выбери образовательную программу и дисциплину.\n"
        "2. Задавай вопросы строго по выбранной теме.\n"
        "3. Получай структурированные и точные ответы.\n\n"

        "📌 <b>Как задавать вопросы правильно?</b>\n"
        "• Вопрос должен быть чётко сформулирован.\n"
        "• Он должен содержать ключевые слова из дисциплины.\n"
        "• Не задавай общих или отвлечённых вопросов — бот ответит только по теме.\n\n"

        "<b>Примеры:</b>\n"
        "✅ «Какие методы используются в медиапланировании?»\n"
        "✅ «Что включает в себя спортивный контент?»\n"
        "❌ «Расскажи что-нибудь»\n"
        "❌ «Привет, как дела?»\n\n"

        "💡 <b>Дополнительно:</b>\n"
        "• За каждый вопрос ты получаешь XP (если нет подписки).\n"
        "• В разделе ℹ️ Info — всё про статусы, бонусы, миссии и подписки.\n\n"
        "📄 <b>Условия использования и оплата:</b>\n"
        "<a href='http://tgbotai.ru/'>Открыть сайт</a>\n\n"
        "Удачи в учёбе и приятной прокачки! 📚"
    )
