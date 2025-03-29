import logging

# Настройка логирования
logger = logging.getLogger('bot_logger')
logger.setLevel(logging.INFO)

# Обработчик для записи в файл
file_handler = logging.FileHandler('bot.log')
file_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# Пример использования логирования
def log_user_activity(user_id, message):
    logger.info(f"User {user_id} performed action: {message}")
