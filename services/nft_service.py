import io
import datetime
import openai
from config import OPENAI_API_KEY, USER_SHEET_NAME, NFT_STATUSES, NFT_FOLDER_ID
from services.google_sheets_service import update_sheet_row
from services.google_drive_service import upload_image_to_drive
from services.user_service import get_user_row_by_id

openai.api_key = OPENAI_API_KEY


def generate_nft_card_if_needed(user_id: str):
    user_data, row_index = get_user_row_by_id(user_id, return_index=True)
    if not user_data or row_index is None:
        return None

    status = user_data.get("status")
    if status not in NFT_STATUSES:
        return None

    nft_statuses_str = user_data.get("nft_statuses", "")
    nft_statuses = [s.strip() for s in nft_statuses_str.split(",") if s.strip()]

    if status in nft_statuses:
        return user_data.get(f"nft_url_{status}")  # Уже есть ссылка

    name = user_data.get("first_name", "Пользователь")
    xp = user_data.get("xp", "0")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # Генерация картинки через DALL·E
    prompt = f"Vector cartoon illustration of a raccoon with glasses, academic cap and book on a pastel background. Title: 'NFT-карточка достижений'. Name: {name}, Status: {status}, XP: {xp}, Date: {date_str}. Flat design."
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )
    image_url = response['data'][0]['url']

    # Загрузка картинки в память
    import requests
    image_bytes = requests.get(image_url).content
    file_name = f"NFT_{status}_{user_id}_{date_str}.png"

    # Загрузка на Google Диск
    drive_url = upload_image_to_drive(file_name, io.BytesIO(image_bytes), folder_id=NFT_FOLDER_ID)

    # Обновление таблицы
    user_data[f"nft_url_{status}"] = drive_url
    nft_statuses.append(status)
    user_data["nft_statuses"] = ", ".join(nft_statuses)
    update_sheet_row(USER_SHEET_NAME, row_index, user_data)

    return drive_url