from services.google_sheets_service import get_sheet_data, update_keywords_for_discipline
from services.gpt_service import generate_ai_response
from config import PROGRAM_SHEETS, PROGRAM_SHEETS_LIST

def generate_keywords_text(module, discipline):
    prompt = (
        f"Ты — методист. Назови 5–10 ключевых слов (через запятую), "
        f"которые точно относятся к дисциплине «{discipline}» модуля «{module}». "
        f"Не используй лишние описания, просто перечисли ключевые слова."
    )
    return generate_ai_response(prompt)

def fill_all_keywords():
    for program_name, sheet_name in PROGRAM_SHEETS_LIST.items():
        print(f"📘 Обрабатываем программу: {program_name}")
        data = get_sheet_data(PROGRAM_SHEETS, f"{sheet_name}!A2:C")
        for row in data:
            if len(row) >= 2:
                module = row[0]
                discipline = row[1]
                current_keywords = row[2] if len(row) >= 3 else ""

                if not current_keywords.strip():
                    print(f"  ➤ Заполняем ключевые слова для: {module} → {discipline}")
                    try:
                        keywords = generate_keywords_text(module, discipline)
                        if keywords:
                            update_keywords_for_discipline(module, discipline, keywords)
                            print(f"    ✅ Успешно: {keywords}")
                        else:
                            print(f"    ⚠️ GPT не вернул ключевые слова для {discipline}")
                    except Exception as e:
                        print(f"    ❌ Ошибка при обработке {discipline}: {e}")

if __name__ == "__main__":
    fill_all_keywords()
