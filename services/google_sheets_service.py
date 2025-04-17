import re
from aiogram import Bot
from config import (
    USER_SHEET_ID, 
    USER_SHEET_NAME, 
    PROGRAM_SHEETS, 
    TOKEN,
    PROGRAM_SHEETS_LIST, 
    PHOTO_LOG_SHEET_NAME,
    IMAGE_LOG_SHEET_NAME
)
from services.sheets import (
    UserRow, 
    get_sheets_service, 
    find_user_row_index,
    get_user_row_by_id, 
    update_sheet_row
) 

from datetime import datetime, timedelta
import pytz

bot = Bot(token=TOKEN)

PLAN_PRIORITY = {
    "lite": 1,
    "pro": 2
}

async def get_all_users() -> list[UserRow]:
    service = get_sheets_service()
    sheet = service.spreadsheets().values()
    result = sheet.get(
        spreadsheetId=USER_SHEET_ID,
        range=USER_SHEET_NAME
    ).execute()

    values = result.get("values", [])
    if not values:
        return []

    headers = values[0]
    header_map = {name: i for i, name in enumerate(headers)}

    user_rows = []
    for idx, row in enumerate(values[1:], start=2):  # начинаем с 2, т.к. первая строка — заголовки
        if row and row[0].isdigit():
            user_rows.append(UserRow(row, header_map, idx))

    return user_rows

async def update_user_plan(user_id: int, new_plan: str, duration_days: int):
    index = await find_user_row_index(str(user_id))
    if index is None:
        print(f"[ERROR] Не найден пользователь с ID {user_id} — update_user_plan отменён")
        return

    row = await get_user_row_by_id(str(user_id))  # возвращает словарь

    current_plan = row.get("plan", "").strip()
    current_until_str = row.get("premium_until", "").strip()

    today = datetime.utcnow()
    new_until = today + timedelta(days=duration_days)

    updates = {}

    # Преобразуем дату окончания текущей подписки
    try:
        current_until = datetime.strptime(current_until_str, "%Y-%m-%d")
    except Exception:
        current_until = today

    # Активная подписка ещё действует?
    if current_until > today:
        # Сравниваем приоритеты
        current_priority = PLAN_PRIORITY.get(current_plan, 0)
        new_priority = PLAN_PRIORITY.get(new_plan, 0)

        if new_plan == current_plan:
            # Просто продлеваем срок
            extended_until = current_until + timedelta(days=duration_days)
            updates = {
                "plan": new_plan,
                "premium_status": new_plan,
                "premium_until": extended_until.strftime("%Y-%m-%d")
            }

        elif new_priority > current_priority:
            # Новый план круче — активируем немедленно
            updates = {
                "plan": new_plan,
                "premium_status": new_plan,
                "premium_until": new_until.strftime("%Y-%m-%d"),
                "next_plan": "",
                "next_until": ""
            }

        else:
            # Новый план слабее — откладываем
            updates = {
                "next_plan": new_plan,
                "next_until": (current_until + timedelta(days=duration_days)).strftime("%Y-%m-%d")
            }

    else:
        # Подписки нет — активируем сразу
        updates = {
            "plan": new_plan,
            "premium_status": new_plan,
            "premium_until": new_until.strftime("%Y-%m-%d"),
            "next_plan": "",
            "next_until": ""
        }

    await update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, index, updates)

async def append_payment_log(row: list):
    SHEET_NAME = "PaymentsLog"

    service = get_sheets_service()
    sheet = service.spreadsheets().values()
    body = {"values": [row]}
    sheet.append(
        spreadsheetId=USER_SHEET_ID,  # ✅ лог записывается в таблицу пользователей
        range=f"{SHEET_NAME}!A:E",
        valueInputOption="RAW",
        body=body
    ).execute()

async def update_payment_status(internal_id: str, new_status: str):
    SHEET_NAME = "PaymentsLog"

    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Предполагаем, что internal_id находится в колонке B
    result = sheet.values().get(
        spreadsheetId=USER_SHEET_ID,
        range=f"{SHEET_NAME}!A:E"
    ).execute()

    values = result.get("values", [])
    for idx, row in enumerate(values):
        if len(row) >= 2 and row[1] == internal_id:
            sheet.values().update(
                spreadsheetId=USER_SHEET_ID,
                range=f"{SHEET_NAME}!E{idx + 1}",
                valueInputOption="RAW",
                body={"values": [[new_status]]}
            ).execute()
            break

async def update_user_xp(user_id: int, xp_add: int):
    row = await get_user_row_by_id(user_id)
    if not row:
        return

    current_xp = int(row.get("xp", 0))
    new_xp = current_xp + xp_add

    i = await row.get_index()
    await update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, {
        "xp": new_xp
    })

def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


async def get_modules_by_program(program_name: str) -> list[str]:
    sheet_name = PROGRAM_SHEETS_LIST.get(program_name)
    if not sheet_name:
        return []

    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=PROGRAM_SHEETS,
            range=f"{sheet_name}!A1:Z1000"
        ).execute()
    except Exception:
        return []

    values = result.get("values", [])
    data_rows = values[1:] if len(values) > 1 else []

    modules = {clean_text(row[0]) for row in data_rows if row and clean_text(row[0])}
    return sorted(modules)

async def get_disciplines_by_module(program: str, module: str) -> list[str]:
    sheet_name = PROGRAM_SHEETS_LIST.get(program)
    if not sheet_name:
        return []

    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=PROGRAM_SHEETS,
        range=f"{sheet_name}"
    ).execute()

    values = result.get("values", [])
    if not values or len(values) < 2:
        return []

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}

    if "Модуль" not in header_map or "Дисциплины" not in header_map:
        return []

    disciplines = set()
    for row in values[1:]:
        mod = clean_text(row[header_map["Модуль"]]) if header_map["Модуль"] < len(row) else ""
        disc = clean_text(row[header_map["Дисциплины"]]) if header_map["Дисциплины"] < len(row) else ""

        if mod == module and disc:
            disciplines.add(disc)

    return sorted(disciplines)

async def get_keywords_for_discipline(program: str, module: str, discipline: str) -> list[str]:
    def clean(text: str) -> str:
        return text.replace('\xa0', ' ').replace('\u200b', '').strip().lower()

    sheet_name = PROGRAM_SHEETS_LIST.get(program)
    if not sheet_name:
        return []

    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=PROGRAM_SHEETS,
        range=f"{sheet_name}"
    ).execute()

    values = result.get("values", [])
    if not values or len(values) < 2:
        return []

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}

    if not all(h in header_map for h in ("Модуль", "Дисциплины", "Ключевые слова")):
        return []

    for row in values[1:]:
        mod = row[header_map["Модуль"]] if header_map["Модуль"] < len(row) else ""
        disc = row[header_map["Дисциплины"]] if header_map["Дисциплины"] < len(row) else ""
        keywords = row[header_map["Ключевые слова"]] if header_map["Ключевые слова"] < len(row) else ""

        if clean(mod) == clean(module) and clean(disc) == clean(discipline):
            return [k.strip().lower() for k in keywords.split(",") if k.strip()]

    return []

async def log_question_answer(user_id: int, program: str, discipline: str, question: str, answer: str):
    service = get_sheets_service()
    values = [[
        str(user_id),
        datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S"),
        program,
        discipline,
        question,
        answer
    ]]
    service.spreadsheets().values().append(
        spreadsheetId=PROGRAM_SHEETS,
        range="QA_Log!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

async def update_keywords_for_discipline(program: str, module: str, discipline: str, keywords: list[str]) -> bool:
    sheet_name = PROGRAM_SHEETS_LIST.get(program)
    if not sheet_name:
        return False

    try:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=PROGRAM_SHEETS,
            range=f"{sheet_name}"
        ).execute()
        values = result.get("values", [])
    except Exception as e:
        return False

    if not values or len(values) < 2:
        return False

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}

    required_columns = ("Модуль", "Дисциплины", "Ключевые слова")
    if not all(h in header_map for h in required_columns):
        return False

    # Ищем строку с нужным модулем и дисциплиной
    for idx, row in enumerate(values[1:], start=2):  # начиная со 2-й строки (1-я — заголовки)
        mod = row[header_map["Модуль"]] if header_map["Модуль"] < len(row) else ""
        disc = row[header_map["Дисциплины"]] if header_map["Дисциплины"] < len(row) else ""

        if mod == module and disc == discipline:
            keywords_cell = ",".join(sorted(set(keywords)))
            range_notation = f"{sheet_name}!{chr(65 + header_map['Ключевые слова'])}{idx}"

            try:
                service.spreadsheets().values().update(
                    spreadsheetId=PROGRAM_SHEETS,
                    range=range_notation,
                    valueInputOption="RAW",
                    body={"values": [[keywords_cell]]}
                ).execute()
                return True
            except Exception as e:
                return False

# Функция для поиска или добавления граф в таблице
async def get_column_index(sheet_id: str, sheet_name: str, column_name: str) -> int:
    service = get_sheets_service()  # Получаем сервис для работы с Google Sheets
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!1:1"  # Получаем первую строку, где находятся заголовки
    ).execute()

    headers = result.get("values", [])[0]  # Считываем заголовки колонок
    if column_name in headers:
        return headers.index(column_name)  # Возвращаем индекс найденной колонки
    else:
        # Если колонка не найдена, создаём новую колонку в конце таблицы
        column_index = len(headers)
        
        # Преобразуем индекс в букву (A, B, C, ..., Z, AA, AB, ...)
        column_letter = chr(65 + column_index) if column_index < 26 else f"{chr(65 + (column_index // 26) - 1)}{chr(65 + (column_index % 26))}"

        # Обновляем таблицу, добавляем новый заголовок в последнюю колонку
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!{column_letter}1",  # Записываем в новую колонку
            valueInputOption="RAW",
            body={"values": [[column_name]]}
        ).execute()
        
        return column_index

async def get_column_value_by_name(sheet_id: str, sheet_name: str, row_index: int, column_name: str) -> str:
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!{column_name}{row_index}"
    ).execute()
    return result.get("values", [])[0][0] if result.get("values") else ""

async def auto_update_expired_subscriptions():
    users = await get_all_users()
    today = datetime.utcnow().date()

    for user in users:
        user_id = user.get("user_id")
        current_until = user.get("premium_until", "")
        next_plan = user.get("next_plan", "").strip()
        next_until = user.get("next_until", "").strip()

        if not (user_id and next_plan and next_until):
            continue

        try:
            until_date = datetime.strptime(current_until, "%Y-%m-%d").date()
            next_date = datetime.strptime(next_until, "%Y-%m-%d").date()
        except:
            continue

        if until_date < today:
            updates = {
                "plan": next_plan,
                "premium_status": next_plan,
                "premium_until": next_until,
                "next_plan": "",
                "next_until": ""
            }
            index = await find_user_row_index(str(user_id))
            if index is not None:
                await update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, index, updates)

                # Уведомление пользователю
                try:
                    await bot.send_message(
                        chat_id=int(user_id),
                        text=f"🔄 Ваша подписка <b>{next_plan.capitalize()}</b> активирована!\n"
                             f"Она будет действовать до <b>{next_until}</b>.",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"[ERROR] Не удалось отправить сообщение пользователю {user_id}: {e}")


async def log_subscription_change(data: dict):
    SHEET_NAME = "SubscriptionLog"
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Получаем заголовки
    result = sheet.values().get(
        spreadsheetId=USER_SHEET_ID,
        range=f"{SHEET_NAME}!1:1"
    ).execute()

    headers = result.get("values", [[]])[0]
    header_map = {name: idx for idx, name in enumerate(headers)}

    # Собираем строку
    row = [""] * len(headers)
    for key, value in data.items():
        idx = header_map.get(key)
        if idx is not None:
            row[idx] = value

    # Добавляем строку в лог
    body = {"values": [row]}
    sheet.values().append(
        spreadsheetId=USER_SHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()


async def auto_update_expired_subscriptions():
    users = await get_all_users()
    today = datetime.utcnow().date()

    for user in users:
        user_id = user.get("user_id")
        current_until = user.get("premium_until", "").strip()
        next_plan = user.get("next_plan", "").strip()
        next_until = user.get("next_until", "").strip()

        if not (user_id and next_plan and next_until):
            continue

        try:
            until_date = datetime.strptime(current_until, "%Y-%m-%d").date()
            next_date = datetime.strptime(next_until, "%Y-%m-%d").date()
        except Exception:
            continue

        if until_date < today:
            index = await find_user_row_index(str(user_id))
            if index is None:
                continue

            # Логика обновления подписки
            updates = {
                "plan": next_plan,
                "premium_status": next_plan,
                "premium_until": next_until,
                "next_plan": "",
                "next_until": ""
            }

            await update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, index, updates)

            # Лог в лист SubscriptionLog
            await log_subscription_change({
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "user_id": str(user_id),
                "activated_plan": next_plan,
                "expires_on": next_until,
                "was_delayed": "Да",
                "previous_plan": user.get("plan", "")
            })

            # Уведомление в Telegram
            try:
                await bot.send_message(
                    chat_id=int(user_id),
                    text=f"🔄 Ваша подписка <b>{next_plan.capitalize()}</b> активирована!\n"
                         f"Она будет действовать до <b>{next_until}</b>.",
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"[ERROR] Не удалось отправить сообщение пользователю {user_id}: {e}")

async def log_photo_request(user_id: int, raw_text: str, answer: str):
    service = get_sheets_service()
    values = [[
        str(user_id),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        raw_text,
        answer,
        "", "", ""
    ]]
    service.spreadsheets().values().append(
        spreadsheetId=PROGRAM_SHEETS,
        range=f"{PHOTO_LOG_SHEET_NAME}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()

async def log_image_request(user_id: int, prompt: str, status: str):
    service = get_sheets_service()
    values = [[
        str(user_id),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        prompt,
        "DALL·E",
        status
    ]]
    service.spreadsheets().values().append(
        spreadsheetId=PROGRAM_SHEETS,
        range=f"{IMAGE_LOG_SHEET_NAME}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values}
    ).execute()
