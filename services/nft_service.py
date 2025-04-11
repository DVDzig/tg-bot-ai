import io
import datetime
import openai
import requests

from openai import AsyncOpenAI
from config import OPENAI_API_KEY, USER_SHEET_NAME, NFT_STATUSES, NFT_FOLDER_ID
from services.google_drive_service import upload_image_to_drive
from services.sheets import update_sheet_row, get_user_row_by_id

openai.api_key = OPENAI_API_KEY

async def generate_nft_card_if_needed(user_id: int):
    user_row = await get_user_row_by_id(user_id)
    if not user_row:
        return None

    status_full = user_row.get("status", "")
    status_clean = status_full.split()[-1]  # достаём слово после эмодзи
    if status_clean not in NFT_STATUSES:
        return None
    status = status_clean

    nft_statuses_str = user_row.get("nft_statuses", "")
    nft_statuses = [s.strip() for s in nft_statuses_str.split(",") if s.strip()]

    if status in nft_statuses:
        return user_row.get(f"nft_url_{status}")  # Уже есть карточка

    name = user_row.get("first_name", "Пользователь")
    xp = user_row.get("xp", "0")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 🎨 Генерация через DALL·E
    prompt = f"Vector cartoon illustration of a raccoon with glasses, academic cap and book on a pastel background. Title: 'NFT-карточка достижений'. Name: {name}, Status: {status}, XP: {xp}, Date: {date_str}. Flat design."
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )
    image_url = response.data[0].url

    # 📥 Скачиваем изображение
    image_bytes = requests.get(image_url).content
    file_name = f"NFT_{status}_{user_id}_{date_str}.png"

    # ☁️ Загружаем в Google Диск
    drive_url = upload_image_to_drive(file_name, io.BytesIO(image_bytes), folder_id=NFT_FOLDER_ID)

    # 📝 Обновляем таблицу
    nft_statuses.append(status)
    updates = {
        f"nft_url_{status}": drive_url,
        "nft_statuses": ", ".join(nft_statuses)
    }

    await update_sheet_row(user_row.sheet_id, user_row.sheet_name, user_row.index, updates)

    return drive_url
