import io
import datetime
import requests
import random
from PIL import Image
from openai import AsyncOpenAI

from config import OPENAI_API_KEY, USER_SHEET_NAME, NFT_STATUSES, NFT_FOLDER_ID
from services.google_drive_service import upload_image_to_drive
from services.sheets import update_sheet_row, get_user_row_by_id

async def generate_nft_card_if_needed(user_id: int):
    user_row = await get_user_row_by_id(user_id)
    if not user_row:
        return None

    status_full = user_row.get("status", "")
    status_clean = status_full.split()[-1]
    if status_clean not in NFT_STATUSES:
        return None
    status = status_clean

    nft_statuses_str = user_row.get("nft_statuses", "")
    nft_statuses = [s.strip() for s in nft_statuses_str.split(",") if s.strip()]

    if status in nft_statuses:
        return user_row.get(f"nft_url_{status}")

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1️⃣ Генерация изображения через DALL·E
    prompt = (
        "A single cute raccoon, boy or girl, with glasses, academic cap and book, "
        "positioned clearly on the RIGHT SIDE of the image. The LEFT SIDE must be empty with a pastel background. "
        "Flat design, vector cartoon, no duplicates, no frame, no crop."
    )

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        response_format="url"
    )
    image_url = response.data[0].url

    # 2️⃣ Скачиваем изображение
    image_bytes = requests.get(image_url).content
    base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # 3️⃣ Загружаем штамп по статусу
    stamp = Image.open(f"stamps/stamp_{status}.png").convert("RGBA")
    stamp = stamp.resize((200, 200))

    # 4️⃣ Выбираем случайный угол
    positions = {
        "top-left": (20, 20),
        "top-right": (804, 20),
        "bottom-left": (20, 804),
        "bottom-right": (804, 804)
    }
    position = random.choice(list(positions.values()))

    # 5️⃣ Вставляем штамп в угол
    base_image.paste(stamp, position, stamp)

    # 6️⃣ Сохраняем результат
    buffer = io.BytesIO()
    base_image.save(buffer, format="PNG")
    buffer.seek(0)

    file_name = f"NFT_{status}_{user_id}_{date_str}.png"
    drive_url = upload_image_to_drive(file_name, buffer, folder_id=NFT_FOLDER_ID)

    # 7️⃣ Обновляем таблицу
    nft_statuses.append(status)
    updates = {
        f"nft_url_{status}": drive_url,
        "nft_statuses": ", ".join(nft_statuses)
    }

    await update_sheet_row(user_row.sheet_id, user_row.sheet_name, user_row.index, updates)
    return drive_url
