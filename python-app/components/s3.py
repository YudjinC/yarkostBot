from minio import Minio
from minio.error import S3Error

from dotenv import load_dotenv
import os

load_dotenv()
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost")
MINIO_PORT = int(os.getenv("MINIO_PORT", 9000))
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "photos")

minio_client = Minio(
    f"{MINIO_ENDPOINT}:{MINIO_PORT}",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
    minio_client.make_bucket(MINIO_BUCKET_NAME)


async def save_photo_to_minio(bot, file_id: str, filename: str) -> str:
    file = await bot.get_file(file_id)
    photo_path = f"/tmp/{filename}"

    await bot.download_file(file_path=file.file_path, destination=photo_path)

    try:
        minio_client.fput_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=filename,
            file_path=photo_path,
            content_type="image/jpeg"
        )
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

    file_url = f"http://{MINIO_ENDPOINT}:{MINIO_PORT}/{MINIO_BUCKET_NAME}/{filename}"
    return file_url
