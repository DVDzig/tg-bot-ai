from config import USER_SHEET_ID
from services.google_sheets_service import get_sheet_data, pad_user_row

_user_cache = {}

def get_user_row(user_id: int):
    if user_id in _user_cache:
        i, row = _user_cache[user_id]
        if i is not None:
            return i, row
        # Если индекс None — принудительно ищем снова

    values = get_sheet_data(USER_SHEET_ID, "Users")
    for i, row in enumerate(values, start=2):
        row = pad_user_row(row)
        if not row or not str(row[0]).strip().isdigit():
            continue  # Пропускаем пустые или некорректные строки
        if str(row[0]) == str(user_id):
            _user_cache[user_id] = (i, row)
            return i, row
    return None, None

def set_user_cache(user_id: int, value: tuple):
    _user_cache[user_id] = value
