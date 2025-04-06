import logging
from fastapi import FastAPI
from aiohttp import web
from starlette.middleware.wsgi import WSGIMiddleware
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import nest_asyncio
nest_asyncio.apply()

from config import TOKEN
from webhook_handler import router as yookassa_router
from handlers import register_all_routers
from middlewares.ensure_user import EnsureUserMiddleware
from utils.scheduler import schedule_all_jobs, schedule_monthly_bonus, schedule_leaderboard_update

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

# === Webhook URL ===
WEBHOOK_PATH = "/webhook"
BASE_WEBHOOK_URL = "https://tg-bot-ai-teyr.onrender.com"
WEBHOOK_SECRET = "supersecret"
WEBHOOK_FULL_URL = BASE_WEBHOOK_URL + WEBHOOK_PATH

async def set_webhook():
    await bot.set_webhook(WEBHOOK_FULL_URL, secret_token=WEBHOOK_SECRET)

@app.get("/")
async def root():
    return {"status": "Bot is running"}

@app.on_event("startup")
async def on_startup():
    logging.info("🚀 Старт Telegram-бота и планировщика")

    # Устанавливаем Webhook
    await set_webhook()

    # Планировщик
    scheduler = AsyncIOScheduler()
    schedule_leaderboard_update(scheduler)
    schedule_all_jobs(bot)
    schedule_monthly_bonus(scheduler)
    scheduler.start()

    # === Интеграция Telegram webhook ===
    aiohttp_app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(
        aiohttp_app, path=WEBHOOK_PATH
    )
    setup_application(aiohttp_app, dp, bot=bot)
    app.mount("/webhook", WSGIMiddleware(aiohttp_app))
