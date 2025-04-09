from aiogram import Router, F
from aiogram.types import Message
from config import ADMIN_ID
from services.google_sheets_service import get_all_users
from keyboards.admin import get_admin_menu_keyboard, get_subscription_choice_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from aiogram.fsm.context import FSMContext
from states.admin_states import GrantSubscription, Broadcast
from services.user_service import activate_subscription, get_status_by_xp
from datetime import datetime, timedelta
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.filter import StateFilter 



router = Router()


@router.message(F.text == "🛠 Админ")
async def show_admin_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к админке.")
        return
    await message.answer(
        "<b>🛠 Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )


@router.message(F.text == "👥 Статистика пользователей")
async def admin_user_stats(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    users = await get_all_users()
    total = len(users)

    lite = sum(1 for u in users if u.get("plan") == "lite")
    pro = sum(1 for u in users if u.get("plan") == "pro")
    free = total - lite - pro

    await message.answer(
        f"📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего: <b>{total}</b>\n"
        f"🔓 Лайт: <b>{lite}</b>\n"
        f"🔐 Про: <b>{pro}</b>\n"
        f"🆓 Без подписки: <b>{free}</b>"
    )


@router.message(F.text == "🏆 Топ по XP")
async def admin_top_xp(message: Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        return

    users = await get_all_users()
    scored = []

    for u in users:
        try:
            xp = int(u.get("xp", 0))
            name = u.get("first_name", "—") or "—"
            user_id = u.get("user_id")
            scored.append((xp, name, user_id))
        except:
            continue

    scored.sort(reverse=True)

    text = "🏆 <b>ТОП-10 пользователей по XP</b>\n\n"
    for idx, (xp, name, uid) in enumerate(scored[:10], start=1):
        status = get_status_by_xp(xp)
        text += f"{idx}. {name} — {status}, {xp} XP (ID: <code>{uid}</code>)\n"

    await message.answer(text)

@router.message(F.text == "🎫 Выдать подписку")
async def choose_subscription_type(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(GrantSubscription.plan_type)
    await message.answer(
        "Выберите тип подписки для выдачи:",
        reply_markup=get_subscription_choice_keyboard()
    )

@router.message(F.text == "🔑 Лайт", GrantSubscription.plan_type)
async def grant_lite(message: Message, state: FSMContext):
    await state.set_state(GrantSubscription.waiting_for_user_id)
    await state.update_data(plan="lite")
    await message.answer("🔢 Введи user_id, кому выдать подписку Лайт:\n\n⬅️ Назад для отмены")

@router.message(F.text == "🔒 Про", GrantSubscription.plan_type)
async def grant_pro(message: Message, state: FSMContext):
    await state.set_state(GrantSubscription.waiting_for_user_id)
    await state.update_data(plan="pro")
    await message.answer("🔢 Введи user_id, кому выдать подписку Про:\n\n⬅️ Назад для отмены")


@router.message(GrantSubscription.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
    if message.text == "🔙 Назад в админ-панель":
        await state.clear()
        await message.answer("🔙 Назад в админ-панель", reply_markup=get_admin_menu_keyboard())
        return

    data = await state.get_data()
    plan = data.get("plan")
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат. Введи только числовой user_id.")
        return

    duration = 7 if plan == "lite" else 30
    until = (datetime.utcnow() + timedelta(days=duration)).strftime("%Y-%m-%d")

    await activate_subscription(user_id=target_id, duration_days=duration, internal_id=f"admin_{plan}")
    await message.answer(f"✅ Подписка <b>{plan.upper()}</b> активирована для пользователя <code>{target_id}</code> до {until}")

    await state.clear()

@router.message(F.text == "🔙 Назад в админ-панель")
async def cancel_subscription(message: Message, state: FSMContext):    
    await state.clear()
    await message.answer("❌ Выдача подписки отменена.", reply_markup=get_admin_menu_keyboard())


@router.message(F.text == "📢 Рассылка")
async def start_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(Broadcast.waiting_for_message)
    await message.answer("📝 Введи текст рассылки. Он будет отправлен всем пользователям.")


@router.message(Broadcast.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext):
    text = message.text
    users = await get_all_users()

    success = 0
    failed = 0

    for u in users:
        user_id = u.get("user_id")
        if not user_id:
            continue
        try:
            await message.bot.send_message(chat_id=int(user_id), text=text)
            success += 1
        except TelegramForbiddenError:
            failed += 1
        except Exception:
            failed += 1

    await message.answer(f"✅ Рассылка завершена:\n\n📤 Отправлено: {success}\n⛔ Ошибок: {failed}")
    await state.clear()


@router.message(F.text == "🔁 Обновить ключевые слова")
async def admin_update_keywords_callback(message: Message, state: FSMContext):

    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⏳ Начинаю обновление ключевых слов...")

    from services.keyword_updater import update_keywords_from_logs
    updated, failed = await update_keywords_from_logs()

    msg = f"✅ Обновление завершено!\n\n"
    msg += f"🔄 Обновлено: <b>{len(updated)}</b>\n"
    msg += f"⚠️ Не удалось обновить: <b>{len(failed)}</b>"

    if failed:
        msg += "\n\n❌ Неудачные дисциплины:\n"
        for f in failed:
            msg += f"• {f}\n"

    await message.answer(msg)

@router.message(F.text == "⬅️ Назад в главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Главное меню", reply_markup=get_main_menu_keyboard(message.from_user.id))
