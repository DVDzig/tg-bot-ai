from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
from config import USER_SHEET_ID, PROGRAM_SHEETS, PROGRAM_SHEETS_LIST, USER_SHEET_NAME, USER_FIELDS


# Подключение к Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'



# Создание API клиента
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)


def format_datetime():
    months = ["января", "февраля", "марта", "апреля", "мая", "июня",
              "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    now = datetime.now()
    return f"{now.day} {months[now.month - 1]} {now.year}, {now.hour:02}:{now.minute:02}"

def get_sheet_data(spreadsheet_id, range_):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_
    ).execute()
    return result.get("values", [])

def append_to_sheet(spreadsheet_id, sheet_name, row_data):
    # Получаем существующие строки
    values = get_sheet_data(spreadsheet_id, f"{sheet_name}!A2:A")
    
    # Ищем первую пустую строку
    row_index = 2
    for i, row in enumerate(values, start=2):
        if not row or not row[0].strip():
            row_index = i
            break
    else:
        row_index = len(values) + 2

    # Запись
    write_to_sheet(spreadsheet_id, sheet_name, pad_user_row(row_data), mode="update", row_index=row_index)

def update_sheet_row(sheet_id, sheet_name, row_index, row_data):
    row_data = pad_user_row(row_data)
    last_col_letter = col_letter(len(row_data))
    range_ = f"{sheet_name}!A{row_index}:{last_col_letter}{row_index}"

    body = {"values": [row_data]}
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_,
        valueInputOption="RAW",
        body=body
    ).execute()

def get_keywords_for_discipline(module, discipline):
    all_sheets = PROGRAM_SHEETS_LIST.values()
    for sheet in all_sheets:
        values = get_sheet_data(PROGRAM_SHEETS, f"{sheet}!A2:C")
        for row in values:
            if isinstance(row, list) and len(row) >= 3 and row[0] == module and row[1] == discipline:
                return row[2]
    return None


def get_leaderboard(top_n=10):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    users = []

    for row in values:
        if not row or not str(row[0]).strip().isdigit():
            continue  # Пропустить пустые или некорректные строки

        if isinstance(row, list) and len(row) < len(USER_FIELDS):
            row += [""] * (len(USER_FIELDS) - len(row))

        try:
            xp_raw = row[USER_FIELDS.index("xp")]
            xp = int(xp_raw) if xp_raw.isdigit() else 0
        except Exception:
            xp = 0

        users.append({
            "user_id": str(row[USER_FIELDS.index("user_id")]),
            "username": row[USER_FIELDS.index("username")],
            "first_name": row[USER_FIELDS.index("first_name")],
            "xp": xp,
            "status": row[USER_FIELDS.index("status")]
        })

    sorted_users = sorted(users, key=lambda x: x["xp"], reverse=True)
    return sorted_users[:top_n]


def get_programs():
    return list(PROGRAM_SHEETS_LIST.keys())

def get_modules(program):
    sheet_name = PROGRAM_SHEETS_LIST.get(program)
    if not sheet_name:
        return []

    values = get_sheet_data(PROGRAM_SHEETS, f"{sheet_name}!A2:A")
    modules = {
        " ".join(row[0].replace("\n", " ").split()).strip()
        for row in values if row and row[0].strip()
    }
    return sorted(modules)

def get_disciplines(module):
    module = " ".join(module.replace("\n", " ").split()).strip().lower()
    disciplines = set()

    for sheet in PROGRAM_SHEETS_LIST.values():
        values = get_sheet_data(PROGRAM_SHEETS, f"{sheet}!A2:B")
        for row in values:
            if isinstance(row, list) and len(row) >= 2:
                row_module = " ".join(row[0].replace("\n", " ").split()).strip().lower()
                if row_module == module:
                    discipline = " ".join(row[1].replace("\n", " ").split()).strip()
                    disciplines.add(discipline)

    return sorted(disciplines)

def log_user_activity(user_id, plan=None, module=None, discipline=None):
    timestamp = datetime.now().strftime("%d %B %Y, %H:%M")
    row = [str(user_id), timestamp, plan or "", module or "", discipline or ""]
    write_to_sheet(USER_SHEET_ID, "Log", row, mode="append")

def update_keywords_for_discipline(module, discipline, keywords):
    all_sheets = PROGRAM_SHEETS_LIST.items()
    updated = False

    for program_name, sheet in all_sheets:
        values = get_sheet_data(PROGRAM_SHEETS, f"{sheet}!A2:C")

        for idx, row in enumerate(values, start=2):
            mod = row[0].strip() if len(row) > 0 else ""
            disc = row[1].strip() if len(row) > 1 else ""

            if mod == module.strip() and disc == discipline.strip():
                range_ = f"{sheet}!C{idx}"
                try:
                    service.spreadsheets().values().update(
                        spreadsheetId=PROGRAM_SHEETS,
                        range=range_,
                        valueInputOption="RAW",
                        body={"values": [[keywords]]}
                    ).execute()
                    updated = True
                except Exception as e:
                    print(f"Ошибка при обновлении Google Sheets: {e}")

                return True

    if not updated:
        print(f"Не найдено совпадения для: {module} — {discipline}")

    return False

def save_question_answer(user_id, program, module, discipline, question, answer):
    timestamp = datetime.now().strftime("%d %B %Y, %H:%M")
    row = [str(user_id), timestamp, program, module, discipline, question, answer]
    write_to_sheet(PROGRAM_SHEETS, "QA_Log", row, mode="append")

def find_similar_questions(discipline, keywords, limit=3):
    discipline = discipline.lower().strip()
    values = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    seen_questions = set()
    similar_qas = []

    for row in values:
        if isinstance(row, list) and len(row) < 7:
            continue

        row_discipline = row[4].lower().strip()
        row_question = row[5].strip()
        row_answer = row[6].strip()

        if row_discipline != discipline:
            continue

        if row_question in seen_questions:
            continue

        if any(kw.lower().strip() in row_question.lower() for kw in (keywords or "").split(",") if kw.strip()):
            seen_questions.add(row_question)
            similar_qas.append({"question": row_question, "answer": row_answer})

        if len(similar_qas) >= limit:
            break

    return similar_qas

def get_all_users():
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:A")
    return [{"user_id": row[0]} for row in values if row]

# Атоматическая подгрузка разрешённых модулей/дисциплин
def get_all_valid_buttons():
    buttons = {
        "🎓 Выбрать программу", "👤 Мой профиль", "🛍 Магазин",
        "📊 ТОП-10", "❓ Помощь", "🔁 Начать сначала", "⬅️ Назад",
        "🔄 Обновить ключевые слова"
    }

    for program in PROGRAM_SHEETS_LIST:
        buttons.add(program)

        sheet = PROGRAM_SHEETS_LIST[program]
        values = get_sheet_data(PROGRAM_SHEETS, f"{sheet}!A2:C")
        for row in values:
            if len(row) > 0:
                buttons.add(f"📗 {row[0]}")  # модуль
            if len(row) > 1:
                buttons.add(f"📕 {row[1]}")  # дисциплина

    return buttons

def log_payment_event(user_id: str, amount: str, questions: str, status: str, event: str, payment_id: str):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    row = [user_id, amount, questions, status, event, payment_id, timestamp]
    write_to_sheet(USER_SHEET_ID, "PaymentsLog", row, mode="append")

def pad_user_row(row: list[str]) -> list[str]:
    if not isinstance(row, list):
        raise TypeError(f"Ожидался список строк, получено: {type(row).__name__}")
    if isinstance(row, list) and len(row) < len(USER_FIELDS):
        row += [""] * (len(USER_FIELDS) - len(row))

    elif len(row) > len(USER_FIELDS):
        row = row[:len(USER_FIELDS)]
    return row

# 🔡 Преобразование номера столбца в букву (A1 формат)
def col_letter(n):
    result = ''
    while n:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result


# 🔍 Получение значения отдельной ячейки
def get_cell_value(spreadsheet_id, sheet_name, row_index, column_index):
    col = col_letter(column_index)
    cell_range = f"{sheet_name}!{col}{row_index}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=cell_range
    ).execute()
    values = result.get("values", [])
    return values[0][0] if values and values[0] else ""

def write_to_sheet(spreadsheet_id, sheet_name, row_data, mode="append", row_index=None):
    row_data = pad_user_row(row_data)

    if mode == "append":
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": [row_data]}
        ).execute()

    elif mode == "update" and row_index:
        last_col = col_letter(len(row_data))
        range_ = f"{sheet_name}!A{row_index}:{last_col}{row_index}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_,
            valueInputOption="RAW",
            body={"values": [row_data]}
        ).execute()

class UserRow:
    def __init__(self, row: list[str]):
        self.row = pad_user_row(row)

    def get(self, field: str, default=""):
        if field not in USER_FIELDS:
            raise ValueError(f"Unknown field: {field}")
        idx = USER_FIELDS.index(field)
        value = self.row[idx]
        return value if value else default

    def get_int(self, field: str, default=0) -> int:
        val = self.get(field, str(default))
        return int(val) if str(val).isdigit() else default

    def set(self, field: str, value):
        if field not in USER_FIELDS:
            raise ValueError(f"Unknown field: {field}")
        idx = USER_FIELDS.index(field)
        self.row[idx] = str(value)

    def add_to_int(self, field: str, amount: int):
        current = self.get_int(field)
        self.set(field, current + amount)

    def data(self) -> list[str]:
        return self.row.copy()

    def save(self, user_id=None):
        if user_id is None:
            user_id = self.get("user_id")
        i, _ = get_user_row(user_id)
        if i is not None:
            update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, self.data())

# === 👤 Вспомогательные функции для пользователей ===

def get_user_row(user_id: int):
    values = get_sheet_data(USER_SHEET_ID, USER_SHEET_NAME)
    for i, row in enumerate(values, start=2):
        row = pad_user_row(row)
        if isinstance(row, list) and str(row[0]).strip() == str(user_id):
            return i, row
    return None, None
