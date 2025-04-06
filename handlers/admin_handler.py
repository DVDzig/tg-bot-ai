from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from config import ADMIN_ID
from services.google_sheets_service import get_all_users
from utils.xp_logic import get_status_by_xp
from keyboards.admin import get_admin_menu_keyboard
from keyboards.main_menu import get_main_menu_keyboard
from aiogram.fsm.context import FSMContext
from states.admin_states import GrantSubscription, Broadcast
from services.user_service import activate_subscription
from datetime import datetime, timedelta
from aiogram.exceptions import TelegramForbiddenError
  

router = Router()


@router.message(F.text == "🔧 Админ")
async def show_admin_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к админке.")
        return
    print(f"\n\U0001f6e0Вход в админку от user_id={message.from_user.id}")

    await message.answer(
        text="Добро пожаловать в админ-панель!",
        reply_markup=get_admin_menu_keyboard()
    )
    
@router.message(F.text == "/users")
async def admin_user_stats(message: Message):
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

@router.message(F.text == "/top")
async def admin_top_xp(message: Message):
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
    
@router.message(F.text == "🛠 Админ")
async def show_admin_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "<b>🛠 Админ-панель</b>\n\nВыберите действие:",
        reply_markup=get_admin_menu_keyboard()
    )

@router.callback_query(F.data == "admin_users")
async def show_user_stats_callback(call: CallbackQuery):
    await call.answer()
    await admin_user_stats(call.message)  # вызываем существующую /users логику

@router.callback_query(F.data == "admin_top")
async def show_admin_top_callback(call: CallbackQuery):
    await call.answer()
    await admin_top_xp(call.message)  # вызываем уже существующую функцию

@router.message(F.text == "/top")
async def admin_top_xp(message: Message):
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

@router.callback_query(F.data == "admin_grant_lite")
async def grant_lite_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(GrantSubscription.waiting_for_user_id)
    await state.update_data(plan="lite")
    await call.message.answer("🔢 Введи user_id, кому выдать подписку Лайт:")

@router.callback_query(F.data == "admin_grant_pro")
async def grant_pro_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(GrantSubscription.waiting_for_user_id)
    await state.update_data(plan="pro")
    await call.message.answer("🔢 Введи user_id, кому выдать подписку Про:")

@router.message(GrantSubscription.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
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

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(Broadcast.waiting_for_message)
    await call.message.answer("📝 Введи текст рассылки. Он будет отправлен всем пользователям.")

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

@router.callback_query(F.data == "admin_back_to_main")
async def back_to_main_menu(call: CallbackQuery):
    await call.answer()
    await call.message.edit_text("🔙 Возвращаемся в главное меню...")
    await call.message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard(call.from_user.id))

@router.callback_query(F.data == "admin_update_keywords")
async def admin_update_keywords_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer("⏳ Начинаю обновление ключевых слов...")
    
    from services.keyword_updater import update_keywords_from_logs
    updated, failed = await update_keywords_from_logs()

    msg = f"✅ Обновление завершено!\n\n"
    msg += f"🔄 Обновлено: <b>{len(updated)}</b>\n"
    msg += f"⚠️ Не удалось обновить: <b>{len(failed)}</b>"

    if failed:
        msg += "\n\n❌ Неудачные дисциплины:\n"
        for f in failed:
            msg += f"• {f}\n"

    await call.message.answer(msg)
    

# 🔍 Логирование всех входящих сообщений (для отладки)
@router.message()
async def fallback_log_all(message: Message):
    print(f"\n🔢 fallback: user_id={message.from_user.id}, text={message.text}")
