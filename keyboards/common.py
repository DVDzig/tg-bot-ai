from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_back_keyboard(from_state: str = None) -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой "⬅️ Назад в магазин". Если передан from_state, может быть расширено в будущем.
    """
    # Можно позже использовать mapping[from_state] для отображения подсказки
    # Пока placeholder один и тот же
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад в магазин")]],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ⤵️"
    )


def get_consultant_keyboard(user_status: str = "") -> ReplyKeyboardMarkup:
    buttons = []

    if user_status in ["Эксперт", "Наставник", "Легенда", "Создатель"]:
        buttons.append([KeyboardButton(text="🎨 Сгенерировать изображение")])

    buttons.append([KeyboardButton(text="🛒 Магазин")])
    buttons.append([KeyboardButton(text="⬅️ Назад в дисциплины")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
