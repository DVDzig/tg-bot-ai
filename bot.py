import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import DefaultBotProperties

from config import TOKEN
from middlewares.ensure_user import EnsureUserMiddleware
from handlers import register_all_routers
from utils.scheduler import schedule_all_jobs

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Инициализация бота с настройками по умолчанию
    bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=TOKEN, default=bot_properties)
    
    # Инициализация диспетчера с памятью
    dp = Dispatcher(bot, storage=MemoryStorage())

    # Middleware для автоматической регистрации пользователей
    dp.message.middleware(EnsureUserMiddleware())
    dp.callback_query.middleware(EnsureUserMiddleware())

    # Регистрация всех роутеров
    register_all_routers(dp)

    # Планировщик фоновых задач (ежедневные миссии, топ и т.д.)
    schedule_all_jobs(bot)

    logger.info("🚀 Бот запущен")
    # Запуск бота
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
