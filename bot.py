import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from middlewares.ensure_user import EnsureUserMiddleware
from handlers import register_all_routers
from utils.scheduler import schedule_all_jobs
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки вебхука
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL", "https://tg-bot-ai-teyr.onrender.com")

# Инициализация бота с настройками по умолчанию
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

async def root_handler(request):
    return web.Response(text="Bot is running!")

async def on_startup(bot: Bot) -> None:
    webhook_url = BASE_WEBHOOK_URL + WEBHOOK_PATH
    await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)
    logging.info(f"Webhook set to {webhook_url}")

async def main():

    
    # Middleware для автоматической регистрации пользователей
    dp.message.middleware(EnsureUserMiddleware())
    dp.callback_query.middleware(EnsureUserMiddleware())

    # Регистрация всех роутеров
    register_all_routers(dp)

    # Планировщик фоновых задач (ежедневные миссии, топ и т.д.)
    schedule_all_jobs(bot)

    # Не запускаем polling, так как используем только вебхук
    logger.info("Бот работает через вебхук.")

if __name__ == "__main__":
    asyncio.run(main())
