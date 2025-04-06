import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.types import WebhookInfo
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from config import TOKEN
from webhook_handler import router as yookassa_router
from handlers import register_all_routers
from middlewares.ensure_user import EnsureUserMiddleware
from utils.scheduler import schedule_all_jobs, schedule_monthly_bonus, schedule_leaderboard_update
from aiogram import types

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI app ===
app = FastAPI()
app.include_router(yookassa_router)

# === Telegram Bot & Dispatcher ===
bot = Bot(token=TOKEN, default={'parse_mode': ParseMode.HTML})
dp = Dispatcher(storage=MemoryStorage())

# Middleware
dp.message.middleware(EnsureUserMiddleware())
dp.callback_query.middleware(EnsureUserMiddleware())

# Роутеры
register_all_routers(dp)

async def set_webhook():
    # Установим webhook
    webhook_url = "https://yourdomain.com/webhook"  # Укажите свой URL
    await bot.set_webhook(webhook_url)

@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Старт Telegram-бота и планировщика")
    
    # Устанавливаем webhook
    await set_webhook()

    # Планировщик
    scheduler = AsyncIOScheduler()
    schedule_leaderboard_update(scheduler)  # Запуск задачи для обновления лидерборда
    schedule_all_jobs(bot)  # Запуск всех других задач
    schedule_monthly_bonus(scheduler)  # Запуск задачи для выдачи месячного бонуса
    
    # Старт планировщика
    scheduler.start()

