import openai
from config import OPENAI_API_KEY, VIDEO_URLS, YOUTUBE_API_KEY
from services.google_sheets_service import get_keywords_for_discipline
from googleapiclient.discovery import build

# Настройка OpenAI
client = openai.OpenAI(api_key=OPENAI_API_KEY)

async def generate_answer(program, module, discipline, user_question) -> str:
    # Составляем промпт
    prompt = (
        f"Ты — преподаватель по дисциплине. Отвечай только по теме дисциплины «{discipline}».\n"
        f"Вопрос: {user_question}"
    )

    # Используем новый интерфейс OpenAI
    chat = await client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ты — преподаватель по дисциплине, помогаешь по дисциплинам."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=800
    )

    return chat.choices[0].message.content.strip()

async def get_video_urls_by_discipline(program, module, discipline, num_videos):
    videos = VIDEO_URLS.get(program, {}).get(module, {}).get(discipline, [])
    return videos[:num_videos]

# Настроим подключение к YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

async def search_video_on_youtube(query: str, max_results: int = 3):
    request = youtube.search().list(
        q=query,
        part="snippet",
        maxResults=max_results,
        type="video"
    )
    response = request.execute()
    video_urls = [
        f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        for item in response["items"]
    ]
    return video_urls
