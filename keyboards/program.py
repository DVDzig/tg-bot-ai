from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎓 Бакалавриат")],
            [KeyboardButton(text="🎓 Магистратура")],
            [KeyboardButton(text="⬅️ Назад в главное меню")]
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
        keyboard=[[KeyboardButton(text=p)] for p in programs] + [[KeyboardButton(text="⬅️ Назад в уровень образования")]],
        resize_keyboard=True
    )

def get_module_keyboard(modules: list[str]):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"🧩 {m}")] for m in modules] + [[KeyboardButton(text="⬅️ Назад в программы")]],
        resize_keyboard=True
    )

def get_discipline_keyboard(disciplines: list[str]):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"🧠 {d}")] for d in disciplines] + [[KeyboardButton(text="⬅️ Назад в модули")]],
        resize_keyboard=True
    )
    
def get_programs_by_level(level: str) -> list[str]:
    if "Бакалавриат" in level:
        return ["📘 МРК", "📗 ТПР", "📙 БХ"]
    elif "Магистратура" in level:
        return ["📕 МСС", "📓 СА", "📔 ФВМ"]
    return []
