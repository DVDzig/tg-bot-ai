def get_status_by_xp(xp: int) -> str:
    if xp >= 5000:
        return "👑 Создатель"
    elif xp >= 1000:
        return "🔥 Легенда"
    elif xp >= 300:
        return "🧠 Наставник"
    elif xp >= 150:
        return "👑 Эксперт"
    elif xp >= 50:
        return "🚀 Профи"
    elif xp >= 10:
        return "🔸 Опытный"
    else:
        return "🟢 Новичок"


def get_next_status(xp: int) -> tuple[str, int]:
    levels = [
        (5000, "👑 Создатель"),
        (1000, "🔥 Легенда"),
        (300, "🧠 Наставник"),
        (150, "👑 Эксперт"),
        (50, "🚀 Профи"),
        (10, "🔸 Опытный"),
        (0, "🟢 Новичок"),
    ]

    for threshold, name in reversed(levels):
        if xp < threshold:
            return name, threshold - xp
    return "👑 Создатель", 0

def get_next_status_info(xp: int) -> tuple[str | None, int | None]:
    levels = [
        (10, "Опытный"),
        (50, "Профи"),
        (150, "Эксперт"),
        (300, "Наставник"),
        (1000, "Легенда"),
        (5000, "Создатель")
    ]

    for level_xp, name in levels:
        if xp < level_xp:
            return name, level_xp - xp
    return None, None
