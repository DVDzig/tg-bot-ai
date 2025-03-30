from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta
from config import USER_SHEET_ID, PROGRAM_SHEETS, PROGRAM_SHEETS_LIST, USER_SHEET_NAME
from functools import lru_cache

# Подключение к Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'

USER_FIELDS = [
    "user_id", "username", "first_name", "last_name", "language_code", "is_premium",
    "first_interaction", "last_interaction",
    "question_count", "day_count", "status", "plan",
    "discipline", "module", "xp", "xp_today", "xp_week",
    "paid_questions", "last_free_reset", "free_questions", "last_bonus_date"
]

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
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1",
        valueInputOption="RAW",
        body={"values": [row_data]}
    ).execute()


def update_sheet_row(spreadsheet_id, sheet_name, row_index, row_data):
    range_ = f"{sheet_name}!A{row_index}:U{row_index}"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption="RAW",
        body={"values": [row_data]}
    ).execute()


@lru_cache(maxsize=512)
def get_keywords_for_discipline(module, discipline):
    all_sheets = PROGRAM_SHEETS_LIST.values()
    for sheet in all_sheets:
        values = get_sheet_data(PROGRAM_SHEETS, f"{sheet}!A2:C")
        for row in values:
            if len(row) >= 3 and row[0] == module and row[1] == discipline:
                return row[2]
    return None


def get_leaderboard(top_n=10):
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:U")
    users = []

    for row in values:
        if len(row) < len(USER_FIELDS):
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
    modules = sorted({row[0].strip() for row in values if len(row) > 0 and row[0].strip()})
    return modules



def get_disciplines(module):
    all_sheets = PROGRAM_SHEETS_LIST.values()
    disciplines = set()
    for sheet in all_sheets:
        values = get_sheet_data(PROGRAM_SHEETS, f"{sheet}!A2:B")
        for row in values:
            if len(row) >= 2 and row[0] == module:
                disciplines.add(row[1])
    return sorted(disciplines)


def log_user_activity(user_id, plan=None, module=None, discipline=None):
    timestamp = datetime.now().strftime("%d %B %Y, %H:%M")
    row = [str(user_id), timestamp, plan or "", module or "", discipline or ""]
    append_to_sheet(USER_SHEET_ID, "Log", row)


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
    append_to_sheet(PROGRAM_SHEETS, "QA_Log", row)


def find_similar_questions(discipline, keywords, limit=3):
    values = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")
    similar_qas = []

    for row in values:
        if len(row) < 7:
            continue

        row_discipline = row[4]
        row_question = row[5]
        row_answer = row[6]

        if row_discipline != discipline:
            continue

        if any(kw.lower() in row_question.lower() for kw in (keywords or "").split(",") if kw.strip()):
            similar_qas.append({"question": row_question, "answer": row_answer})

        if len(similar_qas) >= limit:
            break

    return similar_qas

def get_all_users():
    values = get_sheet_data(USER_SHEET_ID, "Users!A2:A")
    return [{"user_id": row[0]} for row in values if row]
