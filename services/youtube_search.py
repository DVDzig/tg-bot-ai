from googleapiclient.discovery import build
from config import YOUTUBE_API_KEY

def search_youtube_videos(query: str, max_results: int = 1):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            safeSearch="moderate",
        )

        response = request.execute()

        videos = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            videos.append(f"https://www.youtube.com/watch?v={video_id}")

        return videos

    except Exception as e:
        print(f"[YouTube API Error] {e}")
        return []