from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.google_sheets_service import get_programs, get_modules, get_disciplines

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="🎓 Выбрать программу")],
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="💳 Купить доступ")],
        [KeyboardButton(text="📊 Лидерборд"), KeyboardButton(text="❓ Помощь")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_levels_keyboard():
    keyboard = [
        [KeyboardButton(text="🎓 Бакалавриат"), KeyboardButton(text="🎓 Магистратура")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_bachelor_programs_keyboard():
    keyboard = [
        [KeyboardButton(text="📘 МРК"), KeyboardButton(text="📗 ТПР")],
        [KeyboardButton(text="📙 БХ")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_master_programs_keyboard():
    keyboard = [
        [KeyboardButton(text="📕 МСС"), KeyboardButton(text="📗 ФВМ")],
        [KeyboardButton(text="📒 СА")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_programs_keyboard():
    programs = get_programs()
    keyboard = [[KeyboardButton(text=f"📘 {program}")] for program in programs]
    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_modules_keyboard(program: str, include_back=True, is_admin=False):
    modules = get_modules(program)
    keyboard = []
    for module in modules:
        label = module.strip()
        if len(label) > 35:
            parts = label.split(" ")
            half = len(parts) // 2
            label = " ".join(parts[:half]) + "\n" + " ".join(parts[half:])
        keyboard.append([KeyboardButton(text=f"📗 {label}")])

    if is_admin:
        keyboard.append([KeyboardButton(text="🔄 Обновить ключевые слова")])

    if include_back:
        keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_disciplines_keyboard(module: str, include_back=True):
    disciplines = get_disciplines(module)
    keyboard = []
    for discipline in disciplines:
        label = discipline.strip()
        if len(label) > 35:
            parts = label.split(" ")
            half = len(parts) // 2
            label = " ".join(parts[:half]) + "\n" + " ".join(parts[half:])
        keyboard.append([KeyboardButton(text=f"📕 {label}")])

    if include_back:
        keyboard.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_question_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton(text="💳 Купить доступ")]
    ]

    keyboard.append([KeyboardButton(text="⬅️ Назад")])
    keyboard.append([KeyboardButton(text="🔁 Начать сначала")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
