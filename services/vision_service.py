import os
import json
from google.cloud import vision

credentials = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
client = vision.ImageAnnotatorClient.from_service_account_info(credentials)

def extract_text_from_image(image_bytes: bytes) -> str:
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description.strip()
    return ""
