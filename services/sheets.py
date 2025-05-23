from config import USER_SHEET_ID, USER_SHEET_NAME, PROGRAM_SHEETS
from googleapiclient.discovery import build
import json
import os
from google.oauth2.service_account import Credentials
from openpyxl.utils import get_column_letter

_column_cache = {}  # чтобы не запрашивать каждый раз

# ✅ Авторизация через сервисный аккаунт
def get_sheets_service():
    service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

# Получение индекса колонки по названию
async def get_column_index_by_name(sheet_id: str, sheet_name: str, column_name: str) -> int | None:
    key = f"{sheet_id}:{sheet_name}"
    if key not in _column_cache:
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!1:1"
        ).execute()
        headers = result.get("values", [[]])[0]
        _column_cache[key] = {name: idx for idx, name in enumerate(headers)}

    return _column_cache[key].get(column_name)

# Поиск строки пользователя
async def find_user_row_index(user_id: str):
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=USER_SHEET_ID,
        range=f"{USER_SHEET_NAME}!A:A"
    ).execute()

    values = result.get("values", [])
    for i, row in enumerate(values):
        if row and row[0] == user_id:
            return i + 1
    return None

# Обновление строки по ключам
async def update_sheet_row(sheet_id: str, sheet_name: str, row_index: int, updates: dict):
    service = get_sheets_service()
    body = {"valueInputOption": "RAW", "data": []}

    for col_name, value in updates.items():
        col_idx = await get_column_index_by_name(sheet_id, sheet_name, col_name)
        if col_idx is None:
            continue

        col_letter = get_column_letter(col_idx + 1)  # openpyxl — 1-based
        body["data"].append({
            "range": f"{sheet_name}!{col_letter}{row_index}",  # только +1!
            "values": [[value]]
        })

    if body["data"]:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()  
              
# Класс строки пользователя
class UserRow:
    def __init__(self, row: list, header_map: dict, row_index: int):
        self.row = row
        self.header_map = header_map
        self.index = row_index
        self.sheet_id = USER_SHEET_ID
        self.sheet_name = USER_SHEET_NAME

    def get(self, key, default=None):
        idx = self.header_map.get(key)
        if idx is not None and idx < len(self.row):
            return self.row[idx]
        return default

    async def get_index(self):
        return self.index

# Получение строки пользователя по ID
async def get_user_row_by_id(user_id: int) -> UserRow | None:
    service = get_sheets_service()

    if not USER_SHEET_NAME:
        print("[ERROR] USER_SHEET_NAME is None!")
        return None

    try:
        sheet = service.spreadsheets().values()
        result = sheet.get(
            spreadsheetId=USER_SHEET_ID,
            range=f"{USER_SHEET_NAME}"
        ).execute()

        values = result.get("values", [])
        if not values or len(values) < 2:
            return None

        headers = values[0]
        header_map = {name: i for i, name in enumerate(headers)}

        for idx, row in enumerate(values[1:], start=2):
            try:
                if str(user_id) == str(row[0]):
                    return UserRow(row, header_map, idx)
            except IndexError:
                continue

    except Exception as e:
        print(f"[ERROR] get_user_row_by_id(): {e}")
        return None

    return None

async def get_sheet_values_by_column(sheet_name: str, column_name: str) -> list[dict]:
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=PROGRAM_SHEETS,
        range=f"{sheet_name}!A1:Z1000"
    ).execute()

    values = result.get("values", [])
    if not values or len(values) < 2:
        return []

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}
    rows = []

    for row in values[1:]:
        row_dict = {}
        for h, i in header_map.items():
            row_dict[h] = row[i] if i < len(row) else ""
        rows.append(row_dict)

    return rows
