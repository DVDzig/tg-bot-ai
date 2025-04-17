import logging
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.client.default import DefaultBotProperties
from aiogram.types import MenuButtonCommands
from aiogram.types import BotCommand, MenuButtonCommands
from config import TOKEN
from bot import bot

from handlers import (
    start_handler,
    admin_handler,
    info_handler,
    missions_handler,
    profile_handler,
    shop_handler,
    leaderboard_handler,
    program_handler,    
    shop_navigation
)
from middlewares.ensure_user import EnsureUserMiddleware
from utils.scheduler import schedule_all_jobs, schedule_monthly_bonus

dp = Dispatcher(storage=MemoryStorage())

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FastAPI app ===
app = FastAPI()

# === Диспетчеры хендлеров ===
dp.include_router(admin_handler.router)
dp.include_router(info_handler.router)
dp.include_router(missions_handler.router)
dp.include_router(profile_handler.router)
dp.include_router(shop_handler.router)            # ✅ только один shop_handler
dp.include_router(leaderboard_handler.router)
dp.include_router(program_handler.router)
dp.include_router(start_handler.router)
dp.include_router(shop_navigation.router)


# === Telegram Bot & Dispatcher ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Middleware
dp.message.middleware(EnsureUserMiddleware())
dp.callback_query.middleware(EnsureUserMiddleware())

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

    webhook_url = "https://tg-bot-ai-teyr.onrender.com/webhook"
    await bot.set_webhook(webhook_url)

    # 🆕 Устанавливаем команды меню (в поле ввода Telegram)
    await bot.set_my_commands([
        BotCommand(command="start", description="🔄 Начать заново")
    ])
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    # Планировщик задач
    scheduler = AsyncIOScheduler()
    scheduler.start()
