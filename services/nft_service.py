import io
import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
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

    name = user_row.get("first_name", "Пользователь")
    xp = user_row.get("xp", "0")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1️⃣ Генерация изображения через DALL·E
    prompt = (
        "A single cute raccoon with glasses, academic cap and book, "
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

    # 3️⃣ Загружаем шрифты Nunito
    font_regular = ImageFont.truetype("fonts/Nunito-Regular.ttf", size=38)
    font_bold = ImageFont.truetype("fonts/Nunito-Bold.ttf", size=38)
    font_bold_italic = ImageFont.truetype("fonts/Nunito-BoldItalic.ttf", size=36)

    # 4️⃣ Создаем текстовую зону шириной 400px
    text_layer = Image.new("RGBA", (400, base_image.height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_layer)

    lines = [
        ("Статус:", font_bold), (status_full, font_regular),
        ("Имя:", font_bold), (name, font_regular),
        ("XP:", font_bold), (str(xp), font_regular),
        ("Дата:", font_bold), (date_str, font_regular),
        ("@TGTutorBot", font_bold_italic)
    ]

    y = 50
    for text, font in lines:
        draw.text((10, y), text, font=font, fill="#3a3a3a")
        y += 65

    # 5️⃣ Поворачиваем текстовую зону и вставляем точно влево
    rotated_text = text_layer.rotate(90, expand=True)
    final_image = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    final_image.paste(base_image, (0, 0))
    final_image.paste(rotated_text, (0, 0), rotated_text)

    # 6️⃣ Сохраняем результат
    buffer = io.BytesIO()
    final_image.save(buffer, format="PNG")
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