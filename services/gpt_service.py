import openai
from config import OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def generate_ai_response(question, keywords=None, history=None):
    context = ""
    if keywords:
        context += f"Ключевые слова: {keywords}\n"
    if history:
        for pair in tuple(history):  # преобразуем список в tuple для безопасности
            context += f"Q: {pair['question']}\nA: {pair['answer']}\n"
    context += f"\nВопрос пользователя: {question}"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — образовательный консультант. Отвечай по теме, ясно и по существу."},
                {"role": "user", "content": context}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Ошибка при обращении к ИИ: {e}"
