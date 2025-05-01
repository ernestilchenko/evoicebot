from django.conf import settings
from google.cloud import storage


def check_gcs_file_exists(file_path):
    try:
        if file_path.startswith('/'):
            file_path = file_path[1:]

        if file_path.startswith('media/'):
            file_path = file_path[6:]

        if settings.GS_CREDENTIALS:
            client = storage.Client(credentials=settings.GS_CREDENTIALS)
        else:
            client = storage.Client()

        bucket = client.bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(file_path)

        exists = blob.exists()

        if exists:
            size = blob.size
            url = f"https://storage.googleapis.com/{settings.GS_BUCKET_NAME}/{file_path}"
            return True, size, url

        return False, 0, None
    except Exception as e:
        print(f"Error checking GCS file: {str(e)}")
        return False, 0, None
