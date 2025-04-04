from config import USER_SHEET_ID
from services.google_sheets_service import get_sheet_data, pad_user_row

_user_cache = {}

def get_user_row(user_id: int):
    if user_id in _user_cache:
        i, row = _user_cache[user_id]
        if i is not None and row and str(row[0]) == str(user_id):
            return i, row
        # ⚠️ Фикс: продолжим проверку, если строка некорректна

    values = get_sheet_data(USER_SHEET_ID, "Users!A2:Z")
    for i, row in enumerate(values, start=2):
        if not row or len(row) < 1 or not row[0].strip().isdigit():
            continue  # пропускаем полностью пустые строки

        row = pad_user_row(row)
        if str(row[0]).strip() == str(user_id):
            set_user_cache(user_id, (i, row))
            return i, row

    return None, None

def set_user_cache(user_id: int, value: tuple):
    _user_cache[user_id] = value
