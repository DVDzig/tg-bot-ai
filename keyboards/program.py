from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎓 Бакалавриат")],
            [KeyboardButton(text="🎓 Магистратура")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )


def get_program_keyboard(level: str):
    if "Бакалавриат" in level:
        programs = ["📘 МРК", "📗 ТПР", "📙 БХ"]
    elif "Магистратура" in level:
        programs = ["📕 МСС", "📓 СА", "📔 ФВМ"]
    else:
        programs = []

    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=p)] for p in programs] + [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def get_module_keyboard(modules: list[str]):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=m)] for m in modules] + [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def get_discipline_keyboard(disciplines: list[str]):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=d)] for d in disciplines] + [[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )


def get_back_keyboard(from_state: str):
    mapping = {
        "level": "🎓 Бакалавриат / Магистратура",
        "program": "💬 Выбор программы",
        "module": "📘 Программа",
        "discipline": "📘 Дисциплина",
        "context": "Задание вопросов"
    }
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True
    )
