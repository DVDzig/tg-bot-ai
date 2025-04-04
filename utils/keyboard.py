from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from services.google_sheets_service import get_programs, get_modules, get_disciplines

def build_keyboard(button_layout: list[list[str]]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in button_layout],
        resize_keyboard=True
    )

# ——— Статичные клавиатуры ———

main_keyboard = build_keyboard([
    ["🎓 Выбрать программу"],
    ["👤 Мой профиль", "🛍 Магазин"],
    ["📊 Лидерборд", "🎯 Миссии"],
    ["ℹ️ Статусы и подписки", "❓ Помощь"]
])

levels_keyboard = build_keyboard([
    ["🎓 Бакалавриат", "🎓 Магистратура"],
    ["⬅️ Назад"]
])

bachelor_programs_keyboard = build_keyboard([
    ["📘 МРК", "📗 ТПР"],
    ["📙 БХ"],
    ["⬅️ Назад"]
])

master_programs_keyboard = build_keyboard([
    ["📕 МСС", "📗 ФВМ"],
    ["📒 СА"],
    ["⬅️ Назад"]
])

shop_keyboard = build_keyboard([
    ["💬 Вопросы", "💳 Подписка"],
    ["⬅️ Назад"]
])

question_packages_keyboard = build_keyboard([
    ["💡 1 вопрос — 10₽"],
    ["🔥 10 вопросов — 90₽"],
    ["🚀 50 вопросов — 450₽"],
    ["👑 100 вопросов — 900₽"],
    ["⬅️ Назад"]
])

subscription_packages_keyboard = build_keyboard([
    ["💡 Лайт-доступ — 149₽"],
    ["🚀 Про-доступ — 299₽"],
    ["⬅️ Назад"]
])

question_keyboard = build_keyboard([
    ["🛍 Магазин"],
    ["⬅️ Назад"],
    ["🔁 Начать сначала"]
])

# ——— Возвратные функции для клавиатур ———

def get_main_keyboard():
    return main_keyboard

def get_levels_keyboard():
    return levels_keyboard

def get_bachelor_programs_keyboard():
    return bachelor_programs_keyboard

def get_master_programs_keyboard():
    return master_programs_keyboard

def get_shop_keyboard():
    return shop_keyboard

def get_question_packages_keyboard():
    return question_packages_keyboard

def get_subscription_packages_keyboard():
    return subscription_packages_keyboard

def get_question_keyboard(is_admin=False):
    return question_keyboard

# ——— Динамические клавиатуры (модули, дисциплины, программы) ———

def get_programs_keyboard():
    programs = get_programs()
    keyboard = [[f"📘 {program}"] for program in programs]
    keyboard.append(["⬅️ Назад"])
    return build_keyboard(keyboard)

def get_modules_keyboard(program: str, include_back=True, is_admin=False):
    modules = get_modules(program)
    keyboard = []

    for module in modules:
        label = module.strip()
        if len(label) > 35:
            parts = label.split(" ")
            half = len(parts) // 2
            label = " ".join(parts[:half]) + "\n" + " ".join(parts[half:])
        keyboard.append([f"📗 {label}"])

    if is_admin:
        keyboard.append(["🔄 Обновить ключевые слова"])
    if include_back:
        keyboard.append(["⬅️ Назад"])

    return build_keyboard(keyboard)

def get_disciplines_keyboard(module: str, include_back=True):
    disciplines = get_disciplines(module)
    keyboard = []

    for discipline in disciplines:
        label = discipline.strip()
        if len(label) > 35:
            parts = label.split(" ")
            half = len(parts) // 2
            label = " ".join(parts[:half]) + "\n" + " ".join(parts[half:])
        keyboard.append([f"📕 {label}"])

    if include_back:
        keyboard.append(["⬅️ Назад"])

    return build_keyboard(keyboard)
