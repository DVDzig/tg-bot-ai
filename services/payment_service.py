from aiogram import Router, F
from aiogram.types import Message
from services.yookassa_service import generate_payment_link
from config import USER_SHEET_ID
from services.sheets import get_sheets_service
from datetime import datetime


router = Router()

async def log_pending_payment(user_id: int, payment_id: str, quantity: int, payment_type: str):
    # Название листа в Google Sheets, куда будем записывать логи
    SHEET_NAME = "PaymentsLog"
    
    # Получаем сервис для работы с Google Sheets
    service = get_sheets_service()

    # Текущая дата и время для записи в столбец timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Заполнение данных для записи в таблицу
    row = [
        str(user_id),           # Идентификатор пользователя
        str(quantity),          # Количество (вопросов или дней подписки)
        str(payment_type),      # Тип платежа (например, "subscription" или "questions")
        "pending",              # Статус платежа (пока он в ожидании)
        "payment",              # Место для "события" — например, "создание платежа"
        payment_id,             # Уникальный идентификатор платежа
        timestamp               # Время создания записи
    ]
    
    # Создаем тело запроса для записи в таблицу
    body = {"values": [row]}

    # Выполняем запрос на добавление строки в таблицу
    sheet = service.spreadsheets().values()
    sheet.append(
        spreadsheetId=USER_SHEET_ID,   # ID таблицы
        range=f"{SHEET_NAME}!A:G",     # Диапазон, куда записываем данные (все колонки от A до G)
        valueInputOption="RAW",        # Записываем данные как есть
        body=body                      # Данные для записи
    ).execute()

# Обработчик для подписки (Лайт)
@router.message(F.text == "💳 Подписка Лайт (7 дней)")
async def handle_light_subscription_payment(message: Message):
    user_id = message.from_user.id
    amount = 149  # Стоимость подписки Лайт на 7 дней
    description = "Подписка Лайт на 7 дней"

    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты подписки Лайт перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчик для подписки (Про)
@router.message(F.text == "💳 Подписка Про")
async def handle_pro_subscription_payment(message: Message):
    user_id = message.from_user.id
    amount = 299  # Стоимость подписки Про
    description = "Подписка Про"

    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты подписки Про перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчик для покупки 1 вопроса
@router.message(F.text == "💳 Купить 1 вопрос")
async def handle_single_question_purchase(message: Message):
    user_id = message.from_user.id
    amount = 10  # Стоимость 1 вопроса
    description = "Покупка 1 вопроса"

    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты 1 вопроса перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчик для покупки 10 вопросов
@router.message(F.text == "💳 Купить 10 вопросов")
async def handle_ten_questions_purchase(message: Message):
    user_id = message.from_user.id
    amount = 90  # Стоимость 10 вопросов
    description = "Покупка 10 вопросов"

    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты 10 вопросов перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчик для покупки 50 вопросов
@router.message(F.text == "💳 Купить 50 вопросов")
async def handle_fifty_questions_purchase(message: Message):
    user_id = message.from_user.id
    amount = 450  # Стоимость 50 вопросов
    description = "Покупка 50 вопросов"

    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты 50 вопросов перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

# Обработчик для покупки 100 вопросов
@router.message(F.text == "💳 Купить 100 вопросов")
async def handle_hundred_questions_purchase(message: Message):
    user_id = message.from_user.id
    amount = 900  # Стоимость 100 вопросов
    description = "Покупка 100 вопросов"

    try:
        payment_link = await generate_payment_link(amount, description, user_id)
        await message.answer(f"Для оплаты 100 вопросов перейди по ссылке: {payment_link}")
    except Exception as e:
        await message.answer(f"Ошибка при создании платёжной ссылки: {str(e)}")

async def log_successful_payment(user_id: int, quantity: int, payment_type: str, payment_id: str):
    # Логируем успешный платёж
    row = [
        str(user_id),
        payment_id,
        payment_type,
        quantity,
        "success"
    ]
    await append_payment_log(row)
