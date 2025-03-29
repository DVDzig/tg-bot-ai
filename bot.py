import asyncio
import logging
import pytz
from datetime import datetime, time as dt_time, timedelta

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from aiohttp import web

from config import TOKEN
from handlers import start_handler, program_handler, payment_handler
from services.google_sheets_service import get_all_users
from services.user_service import add_paid_questions


# --- Webhook от Robokassa ---
async def handle_payment_webhook(request):
    data = await request.post()
    print("[WEBHOOK RAW DATA]", data)  # 👈 это критично сейчас

    try:
        user_id = int(data.get("Shp_UserID", 0))
        questions = int(data.get("Shp_Questions", 0))
        inv_id = data.get("InvId", "")

        print(f"[WEBHOOK] Оплата от пользователя {user_id} за {questions} вопросов (inv_id: {inv_id})")

        success = add_paid_questions(user_id, questions)
        print(f"[WEBHOOK] Вопросы начислены? {success}")
        return web.Response(text="OK")

    except Exception as e:
        print(f"[Webhook Error] {e}")
        return web.Response(text="Error")


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

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_handler.router)
    dp.include_router(program_handler.router)
    dp.include_router(payment_handler.router)

    # --- Webhook ---
    app = web.Application()
    app.router.add_post("/payment/result", handle_payment_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ Webhook для Robokassa запущен на http://localhost:8080/payment/result")

    # --- Задача напоминания ---
    asyncio.create_task(send_daily_reminder(bot))

    # --- Запуск бота ---
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
