from aiogram import Router, F
from aiogram.types import Message
from keyboards.profile_menu import get_profile_menu_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from services.google_sheets_service import get_user_row_by_id

router = Router()

@router.message(F.text == "👤 Мой профиль")
async def open_profile_menu(message: Message):
    await message.answer("📂 Раздел «Профиль»", reply_markup=get_profile_menu_keyboard())

@router.message(F.text == "👥 Рефералы")
async def show_referrals(message: Message):
    user_id = message.from_user.id
    row = await get_user_row_by_id(user_id)
    if not row:
        await message.answer("Профиль не найден 😔")
        return

    count = int(row.get("referrals_count", 0))
    link = f"https://t.me/TGTutorBot?start=ref_{user_id}"

    await message.answer(
        f"👥 <b>Реферальная программа</b>\n"
        f"Приглашай друзей и получай бонусы! 🎁\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>\n\n"
        f"👨‍👩‍👧 Ты уже пригласил: <b>{count}</b> друзей",
        parse_mode="HTML"
    )

@router.message(F.text == "📄 Мои вопросы")
async def show_user_questions(message: Message):
    from services.google_sheets_service import get_last_user_questions  # импорт внутрь, чтобы избежать циклов

    user_id = message.from_user.id
    questions = await get_last_user_questions(user_id)

    if not questions:
        await message.answer("У тебя пока нет сохранённых вопросов 🤔")
        return

    text = "📄 <b>Твои вопросы:</b>\n\n"
    for i, q in enumerate(questions, 1):
        text += f"{i}. 📘 <b>{q['discipline']}</b> — {q['question'][:50]}...\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "⬅️ Назад")
async def back_to_main_menu(message: Message):
    user_id = message.from_user.id
    await message.answer("⬅️ Возвращаюсь в главное меню", reply_markup=get_main_menu_keyboard(user_id))

@router.message(F.text == "📊 Статистика")
async def show_user_stats(message: Message):
    from services.user_service import get_status_by_xp, get_next_status

    user_id = message.from_user.id
    row = await get_user_row_by_id(user_id)
    if not row:
        await message.answer("Профиль не найден 😔")
        return

    xp = int(row.get("xp", 0))
    day_count = int(row.get("day_count", 0))
    week_count = int(row.get("xp_week", 0))
    total = int(row.get("question_count", 0))
    status = get_status_by_xp(xp)
    next_status, to_next = get_next_status(xp)

    text = (
        f"📊 <b>Твоя статистика:</b>\n\n"
        f"• Сегодня задано: {day_count} вопрос(ов)\n"
        f"• За неделю: {week_count} вопрос(ов)\n"
        f"• Всего: {total} вопрос(ов)\n\n"
        f"• Текущий XP: {xp} XP\n"
        f"• Статус: {status}\n"
        f"• До следующего: {to_next} XP ({next_status})"
    )

    await message.answer(text, parse_mode="HTML")
