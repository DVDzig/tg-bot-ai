from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_back_keyboard(from_state: str = None) -> ReplyKeyboardMarkup:
    """
    Возвращает клавиатуру с кнопкой "⬅️ Назад". Если передан from_state, может быть расширено в будущем.
    """
    # Можно позже использовать mapping[from_state] для отображения подсказки
    # Пока placeholder один и тот же
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие ⤵️"
    )


def get_consultant_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Магазин")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Спроси меня или выбери действие ⤵️"
    )
