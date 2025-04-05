import openai
from config import OPENAI_API_KEY
import os
import logging

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Константы ———
INSTRUCTION_TEXT = (
    "Ты — ИИ-ассистент, который отвечает строго по теме учебной дисциплины.\n"
    "Используй ключевые слова и похожие вопросы, чтобы дать краткий, точный и структурированный ответ.\n\n"
)

MAX_PROMPT_LENGTH = 1000
MAX_QA_HISTORY = 2
MAX_QA_LENGTH = 300


def build_full_prompt(prompt, keywords, similar_qas):
    if not keywords:
        keywords = ""
        similar_qas = []

    trimmed_qas = []
    for item in (similar_qas or [])[:MAX_QA_HISTORY]:
        q = item["question"][:MAX_QA_LENGTH].strip()
        a = item["answer"][:MAX_QA_LENGTH].strip()
        trimmed_qas.append(f"Q: {q}\nA: {a}")

    history_block = "\n\n".join(trimmed_qas)
    user_prompt = prompt.strip()
    if isinstance(user_prompt, str) and len(user_prompt) > MAX_PROMPT_LENGTH:
        user_prompt = user_prompt[:MAX_PROMPT_LENGTH] + "..."

    full_prompt = INSTRUCTION_TEXT
    if history_block:
        full_prompt += f"История похожих вопросов:\n{history_block}\n\n"
    full_prompt += f"Ключевые слова: {keywords}\n\n"
    full_prompt += f"Вопрос пользователя: {user_prompt}"

    return full_prompt


def generate_ai_response(prompt, keywords, similar_qas=None):
    try:
        full_prompt = build_full_prompt(prompt, keywords, similar_qas)

        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — образовательный ИИ-консультант. Отвечай строго по теме, кратко и понятно."
                },
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.5,
            max_tokens=600,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"[GPT Error] {e}")
        return "❌ Ошибка генерации ответа. Попробуй позже."

def handle_question_answer(user_id, question):
    answer = generate_ai_response(question)  # Генерация ответа ИИ
    
    if not answer:
        return "Извините, я не могу ответить на этот вопрос."  # Если ответа нет
    
    # Получаем данные о пользователе
    i, row = get_user_row(user_id)
    if not row:
        return "Пользователь не найден."
    
    # Начисляем XP за каждый вопрос
    xp = int(row[USER_FIELDS.index("xp")])  # Получаем текущий XP пользователя
    xp += 1  # Начисляем XP (1 XP за вопрос)
    row[USER_FIELDS.index("xp")] = str(xp)  # Обновляем XP в данных пользователя
    
    # Определяем новый статус пользователя
    status, _, _ = determine_status(xp)  # Получаем новый статус в зависимости от XP
    row[USER_FIELDS.index("status")] = status  # Обновляем статус в данных пользователя
    
    # Сохраняем обновления в таблице
    update_sheet_row(USER_SHEET_ID, USER_SHEET_NAME, i, row)  # Сохраняем изменения в Google Sheets
    
    return answer  # Возвращаем ответ от ИИ
