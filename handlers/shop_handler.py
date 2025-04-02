from aiogram import Router, types
from aiogram.types import Message
from utils.keyboard import (
    get_main_keyboard,
    get_shop_keyboard,
    get_question_packages_keyboard,
    get_subscription_packages_keyboard
)

router = Router()

@router.message(lambda msg: msg.text == "🛍 Магазин")
async def shop_handler(message: Message):
    await message.answer(
        "🛍 <b>Магазин</b>\n\n"
        "Здесь ты можешь приобрести:\n"
        "• 💬 Пакеты вопросов (начисляют XP)\n"
        "• 💳 Подписки Лайт и Про (безлимит, доп. функции)\n\n"
        "🔔 Про-подписка даёт доступ к YouTube-видео, генерации изображений и приоритету.\n"
        "❗ При подписке XP не начисляется\n\n"
        "Выбери вариант ниже ⤵️",
        parse_mode="HTML",
        reply_markup=get_shop_keyboard()
    )

@router.message(lambda message: message.text == "💬 Вопросы")
async def handle_buy_questions(message: Message):
    print("[DEBUG] 💬 Вопросы нажата")
    await message.answer(
        "💬 <b>Покупка вопросов</b>\n\n"
        "Если у тебя закончились бесплатные вопросы — просто купи дополнительные и продолжай обучение!\n\n"
        "📌 Зачем это нужно:\n"
        "• Получай ответы от ИИ по учебным дисциплинам\n"
        "• XP будет начисляться за каждый вопрос\n"
        "• Возможность прокачиваться, выполнять миссии, открывать достижения\n\n"
        "Выбери нужный пакет ниже 👇",
        parse_mode="HTML",
        reply_markup=get_question_packages_keyboard()
    )

@router.message(lambda message: message.text == "💳 Подписка")
async def handle_buy_subscription(message: Message):
    print("[DEBUG] 💬 Вопросы нажата")
    await message.answer(
        "💳 <b>Подписка</b>\n\n"
        "Подписка снимает все лимиты и даёт доступ к эксклюзивным функциям!\n\n"
        "🎁 Что даёт подписка:\n"
        "• Безлимит на вопросы (не тратятся, XP не начисляется)\n"
        "• 🚀 Про: +100 вопросов, видео, генерация изображений, приоритет\n"
        "• 💡 Лайт: просто безлимит на неделю\n\n"
        "Выбирай нужный тариф ниже 👇",
        parse_mode="HTML",
        reply_markup=get_subscription_packages_keyboard()
    )

@router.message(lambda message: message.text == "⬅️ Назад")
async def back_to_main(message: Message):
    await message.answer("↩️ Возвращаемся в главное меню", reply_markup=get_main_keyboard())