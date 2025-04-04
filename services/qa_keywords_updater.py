from collections import defaultdict
from services.google_sheets_service import get_sheet_data, update_keywords_for_discipline, get_keywords_for_discipline
from services.gpt_service import generate_ai_response
from config import PROGRAM_SHEETS

def update_keywords_from_qa():
    print("\n🔁 Обновляем ключевые слова по логам QA...")

    # Загружаем все QA
    all_qa = get_sheet_data(PROGRAM_SHEETS, "QA_Log!A2:G")  # user_id, timestamp, program, module, discipline, question, answer
    grouped = defaultdict(list)

    for row in all_qa:
        if isinstance(row, list) and len(row) >= 7:
            module = row[3].strip()
            discipline = row[4].strip()
            question = row[5].strip()
            answer = row[6].strip()
            key = (module, discipline)
            grouped[key].append((question, answer))

    for (module, discipline), qa_pairs in grouped.items():
        print(f"\n📚 Обновляем: {module} → {discipline} ({len(qa_pairs)} QA)")
        text = ""
    
        # Используем последние 10 элементов, проверяя, что qa_pairs — это список
        for q, a in qa_pairs[-10:]:
            # Проверка типа данных перед использованием len()
            if isinstance(q, str) and isinstance(a, str):
                text += f"Q: {q}\nA: {a}\n"
            else:
                print(f"⚠️ Пропускаем некорректную пару вопрос-ответ: Q: {q}, A: {a}")
    
        prompt = (
            f"Ты — методист. Проанализируй следующие вопросы и ответы по дисциплине «{discipline}». "
            f"На их основе выдели 200 ключевых слов, которые отражают суть темы. "
            f"Не давай объяснений, просто перечисли через запятую.\n\n{text}"
        )

        try:
            keywords = generate_ai_response(prompt)
            if keywords:
                existing = get_keywords_for_discipline(module, discipline) or ""
                existing_list = [kw.strip() for kw in existing.split(",") if isinstance(kw, str) and kw.strip()]
                new_list = [kw.strip() for kw in keywords.split(",") if isinstance(kw, str) and kw.strip()]
                merged_keywords = sorted(set(existing_list + new_list))
                final_keywords = ", ".join(merged_keywords)

                update_keywords_for_discipline(module, discipline, final_keywords)
                print(f"✅ Ключевые слова добавлены: {len(new_list)} новых → всего {len(merged_keywords)}")
            else:
                print("⚠️ GPT не вернул ключевые слова")
        except Exception as e:
            print(f"❌ Ошибка при обновлении: {e}")

