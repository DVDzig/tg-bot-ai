import asyncio
import logging
import pytz
import aiogram
print("Aiogram version:", aiogram.__version__)

from datetime import datetime, time as dt_time, timedelta
from config import TOKEN
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
from aiogram.fsm.storage.memory import MemoryStorage

from aiohttp import web

from config import TOKEN
from handlers import start_handler, program_handler
from services.google_sheets_service import get_all_users
from services.user_service import add_paid_questions
from services.google_sheets_service import log_payment_event


# --- Webhook от Robokassa ---


async def handle_payment_webhook(request):
    data = await request.json()
    event_type = data.get("event")
    obj = data.get("object", {})

    metadata = obj.get("metadata", {})
    user_id = metadata.get("user_id", "unknown")
    questions = metadata.get("questions", "0")
    amount = obj.get("amount", {}).get("value", "0.00")
    payment_id = obj.get("id", "")
    status = obj.get("status", "unknown")

    print(f"[YooKassa] Event: {event_type} | Status: {status} | User: {user_id} | Questions: {questions}")

    if event_type == "payment.succeeded":
        from services.user_service import add_paid_questions, get_user_profile, determine_status
        success = add_paid_questions(int(user_id), int(questions))
        print(f"[YooKassa] Вопросы зачислены: {success}")
        log_payment_event(user_id, amount, questions, status, event_type, payment_id)

        if success:
            try:
                profile = get_user_profile(int(user_id))
                xp = profile.get("xp", 0)
                current_status, _ = determine_status(xp)
                next_status_info = {
                    "новичок": ("опытный", 11),
                    "опытный": ("профи", 51),
                    "профи": ("эксперт", 101),
                    "эксперт": ("эксперт", 9999)
                }
                next_status, xp_target = next_status_info.get(current_status, ("опытный", 11))
                xp_left = max(0, xp_target - xp)

                # Персонализированное сообщение в зависимости от пакета
                if int(questions) == 1:
                    text = "✅ Ты купил 1 вопрос. Удачи в учебе! 📘"
                elif int(questions) == 10:
                    text = "✅ +10 вопросов добавлены. Ты на пути к знаниям! 🧠"
                elif int(questions) == 50:
                    text = "💥 Целых 50 вопросов теперь у тебя! Ты — машина знаний! 🤖"
                elif int(questions) == 100:
                    text = "👑 100 вопросов — ты явно готов к марафону! Вперёд к успеху!"
                else:
                    text = f"✅ Вопросы ({questions}) успешно начислены!"

                text += f"\n\n🧮 Осталось {xp_left} XP до уровня «{next_status}»."
                text += "\nСпасибо за поддержку ❤️"

                await bot.send_message(
                    chat_id=int(user_id),
                    text=text
                )
            except Exception as e:
                print(f"[YooKassa] Не удалось отправить сообщение пользователю {user_id}: {e}")

        return web.Response(text="OK")

    elif event_type == "payment.canceled":
        log_payment_event(user_id, amount, questions, status, event_type, payment_id)
        print(f"[YooKassa] Платёж отменён пользователем {user_id}")
        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=(
                    "❌ Платёж был отменён.\n"
                    "Если возникли трудности — напиши нам, и мы поможем! 💬"
                )
            )
        except Exception as e:
            print(f"[YooKassa] Не удалось отправить сообщение пользователю {user_id}: {e}")

        return web.Response(text="CANCELLED")

# --- Уведомление о челлендже и напоминание вечером ---  
async def send_daily_reminder(bot: Bot):
    while True:
        now = datetime.now(pytz.timezone("Europe/Moscow"))

        # Утреннее напоминание — в 10:00
        if now.time() >= dt_time(10, 0) and now.time() < dt_time(10, 1):
            users = get_all_users()
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=int(user["user_id"]),
                        text="🧠 Не забудь сегодня выполнить челлендж — задай 3 вопроса и получи бонус!",
                        disable_notification=True
                    )
                except Exception as e:
                    print(f"❌ Утром: не удалось отправить сообщение {user['user_id']}: {e}")
            await asyncio.sleep(60)

        # Вечернее напоминание — в 18:34
        if now.time() >= dt_time(18, 34) and now.time() < dt_time(18, 35):
            users = get_all_users()
            today = now.date()
            for user in users:
                try:
                    last_interaction = user.get("last_interaction", "")
                    if last_interaction:
                        last_date = datetime.strptime(last_interaction, "%Y-%m-%d %H:%M:%S").date()
                        if last_date < today:
                            await bot.send_message(
                                chat_id=int(user["user_id"]),
                                text="📌 Сегодня ты ещё не задавал вопросы — не упусти бонус!",
                                disable_notification=True
                            )
                except Exception as e:
                    print(f"❌ Вечером: не удалось отправить сообщение {user['user_id']}: {e}")
            await asyncio.sleep(60)

        await asyncio.sleep(30)

# --- Основная функция ---
async def main():
    logging.basicConfig(level=logging.INFO)

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_handler.router)
    dp.include_router(program_handler.router)
    # dp.include_router(payment_handler.router) - payment_handler больше не нужен

    # --- Webhook ---
    app = web.Application()
    app.router.add_post("/payment/result", handle_payment_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ Webhook для YooKassa запущен на https://tg-bot-ai-teyr.onrender.com/payment/result")

    # --- Задача напоминания ---
    asyncio.create_task(send_daily_reminder(bot))

    # --- Запуск бота ---
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
