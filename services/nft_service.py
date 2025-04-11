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

    # 1. Генерация изображения через DALL·E
    prompt = (
        "A vector cartoon illustration of a cute raccoon with glasses, academic cap and book, "
        "positioned on the RIGHT SIDE of the image. The LEFT SIDE should be mostly empty with a pastel background, "
        "allowing space for text. Flat design."
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

    # 2. Скачиваем изображение
    image_bytes = requests.get(image_url).content
    base_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # 3. Накладываем текст с помощью PIL
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_main = ImageFont.truetype(font_path, size=40)

    text_image = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_image)

    lines = [f"{status_full}", name, f"XP: {xp}  |  {date_str}"]
    text_y = 40
    for line in lines:
        text_width = draw.textlength(line, font=font_main)
        draw.text((40, text_y), line, font=font_main, fill="#3a3a3a")
        text_y += 60

    text_image = text_image.rotate(90, expand=True)
    final_image = Image.alpha_composite(base_image, text_image.crop((0, 0, base_image.width, base_image.height)))

    # 4. Сохраняем изображение в память
    output_buffer = io.BytesIO()
    final_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    file_name = f"NFT_{status}_{user_id}_{date_str}.png"

    # 5. Загружаем в Google Диск
    drive_url = upload_image_to_drive(file_name, output_buffer, folder_id=NFT_FOLDER_ID)

    # 6. Обновляем таблицу
    nft_statuses.append(status)
    updates = {
        f"nft_url_{status}": drive_url,
        "nft_statuses": ", ".join(nft_statuses)
    }

    await update_sheet_row(user_row.sheet_id, user_row.sheet_name, user_row.index, updates)

    return drive_url