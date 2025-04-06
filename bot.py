import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from middlewares.ensure_user import EnsureUserMiddleware
from handlers import register_all_routers
from utils.scheduler import schedule_all_jobs

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота с настройками по умолчанию
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(bot, storage=MemoryStorage())
    
    # Middleware для автоматической регистрации пользователей
    dp.message.middleware(EnsureUserMiddleware())
    dp.callback_query.middleware(EnsureUserMiddleware())

    # Регистрация всех роутеров
    register_all_routers(dp)

    # Планировщик фоновых задач (ежедневные миссии, топ и т.д.)
    schedule_all_jobs(bot)

    # Настройка вебхука
    webhook_url = "https://tg-bot-ai-teyr.onrender.com/webhook"  # Замените на ваш URL
    await bot.set_webhook(webhook_url)  # Устанавливаем вебхук

    logger.info(f"Вебхук установлен: {webhook_url}")

    # Не запускаем polling, так как используем только вебхук
    logger.info("Бот работает через вебхук.")

if __name__ == "__main__":
    asyncio.run(main())
