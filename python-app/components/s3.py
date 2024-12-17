from minio import Minio
from minio.error import S3Error
import asyncio

from dotenv import load_dotenv
import os

load_dotenv()
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost")
MINIO_PORT = int(os.getenv("MINIO_PORT", 9000))
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "admin")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "photos")
PHOTO_STORAGE_ENDPOINT = os.getenv("PHOTO_STORAGE_ENDPOINT", f"http://{MINIO_ENDPOINT}:9001")

minio_client = Minio(
    f"{MINIO_ENDPOINT}:{MINIO_PORT}",
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

loop = asyncio.get_event_loop()


async def minio_start():
    try:
        bucket_exists = await loop.run_in_executor(None, minio_client.bucket_exists, MINIO_BUCKET_NAME)
        if not bucket_exists:
            await loop.run_in_executor(None, minio_client.make_bucket, MINIO_BUCKET_NAME)
            print(f'[MINIO_INFO] Bucket "{MINIO_BUCKET_NAME}" crate.')
        else:
            print(f'[MINIO_INFO] Bucket "{MINIO_BUCKET_NAME}" exist.')
    except S3Error as e:
        print(f'[MINIO_ERROR] MinIO: {e}')


async def save_photo_to_minio(bot, file_id: str, filename: str, user_id: str) -> str:
    file = await bot.get_file(file_id)
    photo_path = f"/tmp/{filename}"

    await bot.download_file(file_path=file.file_path, destination=photo_path)

    object_name = f'{user_id}/{filename}'
    try:
        await loop.run_in_executor(
            None,
            minio_client.fput_object,
            MINIO_BUCKET_NAME,
            object_name,
            photo_path,
            "image/jpeg"
        )
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

    file_url = f"{PHOTO_STORAGE_ENDPOINT}/{MINIO_BUCKET_NAME}/{object_name}"
    return file_url
