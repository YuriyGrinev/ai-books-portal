import mimetypes
from datetime import timedelta
from typing import BinaryIO, Optional
from uuid import UUID

from minio import Minio
from pydantic import HttpUrl

from ....domain.ports.services.storage import StorageService
from ...config.settings import settings


class MinioStorageService(StorageService):
    """MinIO storage service implementation"""

    def __init__(self):
        self.client = Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure bucket exists, create if not"""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            # Устанавливаем политику публичного доступа для чтения
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                    }
                ]
            }
            self.client.set_bucket_policy(self.bucket_name, policy)

    def _get_object_name(self, entity_type: str, entity_id: UUID, file_name: str) -> str:
        """Get object name for file"""
        extension = file_name.split(".")[-1] if "." in file_name else ""
        return f"{entity_type}/{entity_id}/{file_name}" if extension else f"{entity_type}/{entity_id}/{file_name}.bin"

    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        content_type: str,
        entity_type: str,
        entity_id: UUID
    ) -> HttpUrl:
        """Upload file to storage and return public URL"""
        object_name = self._get_object_name(entity_type, entity_id, file_name)

        # Если content_type не указан, пытаемся определить его
        if not content_type:
            content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        # Загружаем файл
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_name,
            data=file,
            length=-1,  # Автоматически определить размер
            content_type=content_type
        )

        # Возвращаем публичный URL
        return HttpUrl(
            f"{settings.MINIO_URL}/{self.bucket_name}/{object_name}",
            scheme="https" if settings.MINIO_SECURE else "http"
        )

    async def delete_file(self, url: HttpUrl) -> bool:
        """Delete file from storage"""
        try:
            # Извлекаем имя объекта из URL
            object_name = url.path.split(f"/{self.bucket_name}/")[-1]
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except Exception:
            return False

    async def get_download_url(self, url: HttpUrl, expires_in: int = 3600) -> Optional[HttpUrl]:
        """Get temporary download URL for file"""
        try:
            # Извлекаем имя объекта из URL
            object_name = url.path.split(f"/{self.bucket_name}/")[-1]
            
            # Получаем временный URL для скачивания
            presigned_url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires_in)
            )
            
            return HttpUrl(presigned_url)
        except Exception:
            return None 