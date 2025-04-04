# services/user_helpers.py

from config import USER_SHEET_ID
from services.google_sheets_service import get_sheet_data, pad_user_row

_user_cache = {}

def get_user_row(user_id: int):
    if user_id in _user_cache:
        return _user_cache[user_id]

    values = get_sheet_data(USER_SHEET_ID, "Users")
    for i, row in enumerate(values, start=2):
        row = pad_user_row(row)
        if str(row[0]) == str(user_id):
            _user_cache[user_id] = (i, row)
            return i, row
    return None, None

def set_user_cache(user_id: int, value: tuple):
    _user_cache[user_id] = value
