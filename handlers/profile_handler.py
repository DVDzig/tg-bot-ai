from aiogram import Router, F
from aiogram.types import Message
from keyboards.profile_menu import get_profile_menu_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from services.google_sheets_service import get_user_row_by_id, get_last_user_questions
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    share_url = f"https://t.me/share/url?url={link}&text=Присоединяйся к образовательному помощнику!"

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поделиться", url=share_url)]
        ]
    )

    await message.answer(
        f"👥 <b>Реферальная программа</b>\n"
        f"Приглашай друзей и получай крутые бонусы! 🎁\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>\n\n"
        f"👨‍👩‍👧 Ты уже пригласил: <b>{count}</b> друзей\n\n"
        f"🏆 <b>Бонусы за приглашения:</b>\n"
        f"• 1 друг — 🎫 +5 бесплатных вопросов\n"
        f"• 3 друга — 💡 Подписка <b>Лайт</b> на 3 дня\n"
        f"• 10 друзей — 🧿 NFT-карточка <b>Амбассадор</b>\n"
        f"• 50 друзей — 👑 Подписка <b>Про</b> на 30 дней\n\n"
        f"📣 Делись ссылкой и получай всё это первым!",
        parse_mode="HTML",
        reply_markup=inline_kb
    )

@router.message(F.text == "📄 Мои вопросы")
async def show_user_questions(message: Message):
    
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

@router.message(F.text == "🏅 Достижения")
async def show_achievements(message: Message):

    user_id = message.from_user.id
    row = await get_user_row_by_id(user_id)
    if not row:
        await message.answer("Профиль не найден 😔")
        return

    raw_achievements = row.get("achievements", "")
    user_achievements = set(a.strip() for a in raw_achievements.split(",") if a.strip())

    # Список всех достижений
    ALL_ACHIEVEMENTS = {
        "first_question": "🎉 Первый вопрос",
        "xp100": "💯 100 XP",
        "mentor": "🧠 Наставник",
        "streak3": "🔥 Серия из 3 дней",
        "q10": "🗣 10 вопросов"
    }

    lines = ["🏅 <b>Твои достижения:</b>\n"]
    for key, label in ALL_ACHIEVEMENTS.items():
        status = "✅" if key in user_achievements else "❌"
        lines.append(f"{status} {label}")

    await message.answer("\n".join(lines), parse_mode="HTML")
