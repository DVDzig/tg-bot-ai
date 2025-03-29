from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.google_sheets_service import get_programs, get_modules, get_disciplines

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="🎓 Выбрать программу")],
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="💰 Купить вопросы")],
        [KeyboardButton(text="📊 Лидерборд"), KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="🔁 Начать сначала")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_programs_keyboard():
    programs = get_programs()
    keyboard = [[KeyboardButton(text=f"📘 {program}")] for program in programs]
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    keyboard.append([KeyboardButton(text="🔁 Начать сначала")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_modules_keyboard(program: str, include_back=True, is_admin=False):
    modules = get_modules(program)
    keyboard = [[KeyboardButton(text=f"📗 {module}")] for module in modules]

    if is_admin:
        keyboard.append([KeyboardButton(text="🔄 Обновить ключевые слова")])

    if include_back:
        keyboard.append([KeyboardButton(text="⬅️ Назад")])

    keyboard.append([KeyboardButton(text="🔁 Начать сначала")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_disciplines_keyboard(module: str, include_back=True):
    disciplines = get_disciplines(module)
    keyboard = [[KeyboardButton(text=f"📕 {discipline}")] for discipline in disciplines]
    if include_back:
        keyboard.append([KeyboardButton(text="⬅️ Назад")])
    keyboard.append([KeyboardButton(text="🔁 Начать сначала")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_question_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton(text="💰 Купить вопросы")]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="🔄 Обновить ключевые слова")])

    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    keyboard.append([KeyboardButton(text="🔁 Начать сначала")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
