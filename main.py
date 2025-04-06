import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from handlers import (
    register_all_routers,
    start_handler,
    admin_handler,
    info_handler,
    missions_handler,
    profile_handler,
    payment_handler,
    shop_handler,
    shop_questions_handler,
    shop_subscription_handler,
    leaderboard_handler
)
from middlewares.ensure_user import EnsureUserMiddleware
from utils.scheduler import schedule_all_jobs, schedule_monthly_bonus, schedule_leaderboard_update

dp = Dispatcher(storage=MemoryStorage())

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI app ===
app = FastAPI()

# === Диспетчеры хендлеров ===
dp.include_router(start_handler.router)
dp.include_router(admin_handler.router)
dp.include_router(info_handler.router)
dp.include_router(missions_handler.router)
dp.include_router(profile_handler.router)
dp.include_router(payment_handler.router)
dp.include_router(shop_handler.router)
dp.include_router(shop_questions_handler.router)
dp.include_router(shop_subscription_handler.router)
dp.include_router(leaderboard_handler.router)

# === Telegram Bot & Dispatcher ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Middleware
dp.message.middleware(EnsureUserMiddleware())
dp.callback_query.middleware(EnsureUserMiddleware())

# Роутеры
register_all_routers(dp)

# === Webhook endpoint ===
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logger.exception("Ошибка при обработке вебхука")
        return {"error": str(e)}

# === Root endpoint (для проверки Render) ===
@app.get("/")
async def root():
    return {"status": "Bot is running"}

@app.head("/")
async def root_head():
    return

# === Startup event ===
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Запуск Telegram-бота и планировщика")

    # Устанавливаем Webhook
    webhook_url = "https://tg-bot-ai-teyr.onrender.com/webhook"
    await bot.set_webhook(webhook_url)

    # Планировщик
    scheduler = AsyncIOScheduler()
    schedule_all_jobs(bot)
    schedule_monthly_bonus(scheduler)
    schedule_leaderboard_update(scheduler)
    scheduler.start()