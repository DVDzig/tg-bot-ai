import json
import io
import mimetypes

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from config import client_email, GOOGLE_CREDENTIALS_JSON

SCOPES = ['https://www.googleapis.com/auth/drive']

# Загрузка credentials из строки в .env
info = json.loads(GOOGLE_CREDENTIALS_JSON)
creds = Credentials.from_service_account_info(info, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def upload_image_to_drive(filename, file_bytes_io, folder_id=None):
    mime_type, _ = mimetypes.guess_type(filename)
    media = MediaIoBaseUpload(file_bytes_io, mimetype=mime_type, resumable=True)

    file_metadata = {
        'name': filename,
        'parents': [folder_id] if folder_id else []
    }

    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    # Сделать файл публичным
    drive_service.permissions().create(
        fileId=uploaded_file['id'],
        body={
            'role': 'reader',
            'type': 'anyone'
        }
    ).execute()

    return f"https://drive.google.com/uc?id={uploaded_file['id']}"

def extract_text_with_docs_ocr(file_bytes: BytesIO, file_name: str = "ocr_image.png", folder_id: str = None) -> str:
    from services.gdrive_auth import get_drive_service
    drive_service = get_drive_service()

    # Загружаем файл как image/png
    file_metadata = {
        "name": file_name,
        "mimeType": "application/vnd.google-apps.document"
    }
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(file_bytes, mimetype="image/png", resumable=True)

    # Конвертируем в Google Docs с OCR
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = file.get("id")

    # Читаем текст из Google Docs
    doc = drive_service.files().export(
        fileId=file_id,
        mimeType="text/plain"
    ).execute()

    # Удаляем временный файл
    drive_service.files().delete(fileId=file_id).execute()

    return doc.decode("utf-8")
