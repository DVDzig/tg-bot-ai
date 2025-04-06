import asyncio
import logging
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
    bot = Bot(token=TOKEN, default={'parse_mode': ParseMode.HTML})  # Изменено
    
    # Инициализация диспетчера с памятью
    dp = Dispatcher(storage=MemoryStorage())  # Используем аргументы как ключевые параметры
    
    # Настроим параметр по умолчанию
    bot.set_my_commands([  # Это тоже лучше оставить как есть
        {"command": "start", "description": "Start the bot"},
    ])
    bot.default_parse_mode = ParseMode.HTML  # Задаём по умолчанию parse_mode для сообщений

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

# === Вебхук обработчик ===
@app.post("/webhook")
async def webhook_handler(request: Request):
    json_data = await request.json()  # Получаем данные от Telegram
    update = Update(**json_data)  # Преобразуем JSON в объект Update
    await dp.process_update(update)  # Передаем обновление в Dispatcher

    return {"status": "ok"}  # Ответ Telegram серверу