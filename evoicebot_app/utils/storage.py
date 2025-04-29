from django.conf import settings
from google.cloud import storage
import os


def check_gcs_file_exists(file_path):
    """
    Проверяет существование файла в Google Cloud Storage

    Args:
        file_path (str): Путь к файлу относительно корня бакета

    Returns:
        tuple: (exists, size, url) - существует ли файл, его размер и URL
    """
    try:
        # Удаляем начальный слеш, если есть
        if file_path.startswith('/'):
            file_path = file_path[1:]

        # Убираем префикс медиа из пути, если есть
        if file_path.startswith('media/'):
            file_path = file_path[6:]

        # Создание клиента хранилища
        if settings.GS_CREDENTIALS:
            client = storage.Client(credentials=settings.GS_CREDENTIALS)
        else:
            client = storage.Client()

        # Получение бакета и блоба
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(file_path)

        # Проверка существования
        exists = blob.exists()

        if exists:
            # Получение размера и URL
            size = blob.size
            url = f"https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{file_path}"
            return True, size, url

        return False, 0, None
    except Exception as e:
        print(f"Error checking GCS file: {str(e)}")
        return False, 0, None