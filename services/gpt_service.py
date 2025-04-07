from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
import openai  # для обработки ошибок

from config import OPENAI_API_KEY, VIDEO_URLS, YOUTUBE_API_KEY
from services.google_sheets_service import get_keywords_for_discipline
from googleapiclient.discovery import build

client = AsyncOpenAI()

async def generate_answer(program: str, module: str, discipline: str, user_question: str) -> str:
    try:
        chat: ChatCompletion = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Ты ИИ-консультант. Отвечай только по дисциплине: {discipline} модуля {module} программы {program}."},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return chat.choices[0].message.content.strip()

    except openai.RateLimitError:
        return "⚠️ Превышен лимит обращений к ИИ. Попробуй позже."
    except openai.AuthenticationError:
        return "🚫 Ошибка авторизации. Проверь OpenAI API ключ."
    except openai.APIConnectionError:
        return "🔌 Проблемы с подключением к OpenAI. Повтори попытку позже."
    except openai.APIError as e:
        return f"⚠️ Ошибка на стороне OpenAI: {e}"
    except Exception as e:
        return f"❌ Произошла ошибка при обращении к ИИ: {e}"

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
