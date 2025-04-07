from config import USER_SHEET_ID, USER_SHEET_NAME, PROGRAM_SHEETS
from services.sheets import (
    UserRow, 
    get_sheets_service, 
    find_user_row_index,
    get_user_row_by_id, 
    update_sheet_row
) 
from datetime import datetime
from config import PROGRAM_SHEETS_LIST

async def get_all_users() -> list[UserRow]:
    service = get_sheets_service()
    sheet = service.spreadsheets().values()
    result = sheet.get(
        spreadsheetId=PROGRAM_SHEETS,
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

async def update_user_plan(user_id: int, plan_type: str, until_date: str):
    index = await find_user_row_index(str(user_id))  # строка в таблице
    if index is None:
        return

    updates = {
        "plan": plan_type,
        "premium_status": plan_type,
        "premium_until": until_date
    }

    await update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, index, updates)

async def append_payment_log(row: list):
    SHEET_NAME = "PaymentsLog"

    service = get_sheets_service()  # предполагается, что эта функция уже есть
    sheet = service.spreadsheets().values()
    body = {"values": [row]}
    sheet.append(
        spreadsheetId=PROGRAM_SHEETS,
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
        spreadsheetId=PROGRAM_SHEETS,
        range=f"{SHEET_NAME}!A:E"
    ).execute()

    values = result.get("values", [])
    for idx, row in enumerate(values):
        if len(row) >= 2 and row[1] == internal_id:
            sheet.values().update(
                spreadsheetId=PROGRAM_SHEETS,
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

    except Exception as e:
        return []

    values = result.get("values", [])
    data_rows = values[1:] if len(values) > 1 else []
    modules = [row[0] for row in data_rows if row and row[0].strip()]
    unique_modules = list(sorted(set(modules)))

    return unique_modules

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

    disciplines = []
    for row in values[1:]:
        mod = row[header_map["Модуль"]] if header_map["Модуль"] < len(row) else ""
        disc = row[header_map["Дисциплины"]] if header_map["Дисциплины"] < len(row) else ""

        if mod == module and disc:
            disciplines.append(disc)

    return sorted(set(disciplines))

async def get_keywords_for_discipline(program: str, module: str, discipline: str) -> list[str]:
    sheet_name = PROGRAM_SHEETS_LIST.get(program)
    if not sheet_name:
        return []

    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        preadsheetId=PROGRAM_SHEETS,
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

        if mod == module and disc == discipline:
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
