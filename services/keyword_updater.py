import openai
from collections import defaultdict
from services.google_sheets_service import (
    get_keywords_for_discipline,
    update_keywords_for_discipline
)
from config import PROGRAM_SHEETS, OPENAI_API_KEY
from services.sheets import get_sheets_service

openai.api_key = OPENAI_API_KEY


async def update_keywords_from_logs():
    service = get_sheets_service()
    qa_data = service.spreadsheets().values().get(
        spreadsheetId=PROGRAM_SHEETS,
        range="QA_Log!A1:Z1000"
    ).execute()

    values = qa_data.get("values", [])
    if not values or len(values) < 2:
        return [], ["Данных в QA_Log нет"]

    headers = values[0]
    header_map = {h: i for i, h in enumerate(headers)}

    grouped = defaultdict(list)

    # Проверка наличия нужных столбцов
    required = ["program", "module", "discipline", "question", "answer"]
    if not all(col in header_map for col in required):
        return [], ["Отсутствуют нужные столбцы в QA_Log"]

    # Группируем вопросы+ответы по (программа, модуль, дисциплина)
    for row in values[1:]:
        try:
            program = row[header_map["program"]]
            module = row[header_map["module"]]
            discipline = row[header_map["discipline"]]
            question = row[header_map["question"]]
            answer = row[header_map["answer"]]
        except IndexError:
            continue

        key = (program, module, discipline)
        grouped[key].append(f"{question}\n{answer}")

    updated = []
    failed = []

    for (program, module, discipline), text_blocks in grouped.items():
        combined_text = "\n".join(text_blocks)[:4000]  # ограничим GPT вход

        prompt = (
            f"Проанализируй текст (вопросы и ответы по дисциплине «{discipline}»). "
            f"Выдели 250-300 ключевых слов или фраз (по теме), разделённых запятыми.\n\n"
            f"{combined_text}"
        )

        try:
            response = openai.ChatCompletion.create(
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
            combined = list(sorted(set(existing + new_keywords)))

            await update_keywords_for_discipline(program, module, discipline, combined)
            updated.append(f"{program} / {module} / {discipline}")

        except Exception as e:
            failed.append(f"{program} / {module} / {discipline} ❌ ({str(e)[:60]}...)")

    return updated, failed

MAX_MESSAGE_LENGTH = 4096

async def send_long_message(text: str, message):
    for i in range(0, len(text), MAX_MESSAGE_LENGTH):
        await message.answer(text[i:i+MAX_MESSAGE_LENGTH])
