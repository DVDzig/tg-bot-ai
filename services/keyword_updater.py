from collections import defaultdict
from datetime import datetime
from openai import OpenAI
from services.google_sheets_service import (
    get_keywords_for_discipline,
    update_keywords_for_discipline    
)
from services.sheets import (
    get_sheets_service, 
    update_sheet_row, 
    get_column_index_by_name
)
from config import PROGRAM_SHEETS, OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

DATE_FORMAT = "%d %B %Y, %H:%M"

async def update_keywords_from_logs():
    service = get_sheets_service()
    sheet = service.spreadsheets().values()

    # 1. Загружаем QA_Log
    data = sheet.get(
        spreadsheetId=PROGRAM_SHEETS,
        range="QA_Log!A1:Z1000"
    ).execute()

    values = data.get("values", [])
    if not values or len(values) < 2:
        return [], ["QA_Log пуст или нет данных"]

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}

    required = ["program", "module", "discipline", "question", "answer", "timestamp"]
    if not all(h in header_map for h in required):
        return [], ["Не хватает нужных столбцов в QA_Log"]

    # 2. Сгруппировать по (program, module, discipline)
    grouped = defaultdict(list)
    last_asked_map = {}
    row_map = defaultdict(list)

    for idx, row in enumerate(values[1:], start=2):  # начиная со второй строки
        try:
            program = row[header_map["program"]]
            module = row[header_map["module"]]
            discipline = row[header_map["discipline"]]
            question = row[header_map["question"]]
            answer = row[header_map["answer"]]
            timestamp_raw = row[header_map["timestamp"]]
            timestamp = datetime.strptime(timestamp_raw, DATE_FORMAT)
        except Exception:
            continue

        key = (program, module, discipline)
        grouped[key].append(f"{question}\n{answer}")
        row_map[key].append(idx)

        # сохраняем последний timestamp по ключу
        if key not in last_asked_map or timestamp > last_asked_map[key]:
            last_asked_map[key] = timestamp

    updated = []
    failed = []

    # Проверяем и сравниваем с last_updated
    last_updated_col = await get_column_index_by_name(PROGRAM_SHEETS, "QA_Log", "last_updated")

    for key, text_blocks in grouped.items():
        program, module, discipline = key
        last_asked = last_asked_map[key]
        rows = row_map[key]

        # находим дату последнего обновления по первым совпадающим строкам
        last_updated = None
        for row_idx in rows:
            try:
                row_data = values[row_idx - 1]
                raw_date = row_data[last_updated_col] if last_updated_col < len(row_data) else ""
                if raw_date:
                    last_updated = datetime.strptime(raw_date, DATE_FORMAT)
                    break
            except:
                continue

        if last_updated and (datetime.now() - last_updated).days < 7:
            print(f"⏭ Пропускаем: {program} / {module} / {discipline} — обновлялось менее 7 дней назад")
            continue


        print(f"🧠 Обновляем: {program} / {module} / {discipline}")
        combined_text = "\n".join(text_blocks)[:4000]

        prompt = (
            f"Проанализируй текст (вопросы и ответы по дисциплине «{discipline}»). "
            f"Выдели 250-300 ключевых слов или фраз, разделённых запятыми.\n\n"
            f"{combined_text}"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты — помощник по анализу учебных данных."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )

            new_keywords_raw = response.choices[0].message.content.strip()
            new_keywords = [kw.strip() for kw in new_keywords_raw.split(",") if kw.strip()]

            if not new_keywords:
                failed.append(f"{program} / {module} / {discipline} (GPT вернул пусто)")
                continue

            existing = await get_keywords_for_discipline(program, module, discipline)
            combined_keywords = list(sorted(set(existing + new_keywords)))

            await update_keywords_for_discipline(program, module, discipline, combined_keywords)
            updated.append(f"{program} / {module} / {discipline}")

            # записываем дату обновления
            now_str = datetime.now().strftime(DATE_FORMAT)
            for idx in rows:
                await update_sheet_row(PROGRAM_SHEETS, "QA_Log", idx, {
                    "last_updated": now_str
                })

        except Exception as e:
            failed.append(f"{program} / {module} / {discipline} ❌ ({str(e)[:60]}...)")

    return updated, failed

MAX_MESSAGE_LENGTH = 4096

async def send_long_message(text: str, message):
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        await message.answer(text[i:i+MAX_MESSAGE_LENGTH])
