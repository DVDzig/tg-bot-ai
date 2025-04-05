import openai
from config import OPENAI_API_KEY, VIDEO_URLS, YOUTUBE_API_KEY
from google_sheets_service import get_keywords_for_discipline
from googleapiclient.discovery import build

openai.api_key = OPENAI_API_KEY

async def generate_answer(program, module, discipline, user_question) -> str:
    # Можно собрать системное сообщение
    prompt = (
        f"Ты — образовательный помощник. Отвечай только по теме дисциплины «{discipline}».\n"
        f"Вопрос: {user_question}"
    )

    # Генерация ответа через OpenAI
    import openai
    from config import OPENAI_API_KEY
    openai.api_key = OPENAI_API_KEY

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ты — образовательный ассистент, помогаешь по дисциплинам."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=800
    )

    answer = response.choices[0].message.content.strip()
    return answer

async def get_video_urls_by_discipline(program, module, discipline, num_videos):
    # Возвращаем только нужное количество видео по дисциплине
    # VIDEO_URLS — словарь, где ключи: программа, модуль, дисциплина, а значения — ссылки на видео
    videos = VIDEO_URLS.get(program, {}).get(module, {}).get(discipline, [])
    
    return videos[:num_videos]

# Настроим подключение к API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

async def search_video_on_youtube(query: str, max_results: int = 3):
    # Запрос к YouTube API для поиска видео
    request = youtube.search().list(
        q=query,  # запрос (ключевые слова из дисциплины/вопроса)
        part="snippet",
        maxResults=max_results,
        type="video"
    )
    
    response = request.execute()

    # Получаем URL видео
    video_urls = [
        f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        for item in response["items"]
    ]

    return video_urls