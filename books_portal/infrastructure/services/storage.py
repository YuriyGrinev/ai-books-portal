import mimetypes
from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO, Optional
from urllib.parse import urljoin, urlparse
from uuid import UUID

from minio import Minio
from minio.error import S3Error

from books_portal.domain.interfaces.storage import FileInfo, StorageService
from books_portal.infrastructure.config.settings import settings


@dataclass
class MinioFileInfo(FileInfo):
    """Информация о файле в MinIO"""
    content_type: str
    size: int


class MinioStorageService(StorageService):
    """Сервис хранения файлов на основе MinIO"""

    # Максимальный размер файла (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # Разрешенные типы контента
    ALLOWED_CONTENT_TYPES = {
        # Изображения
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        # Документы
        "application/pdf",
        "application/epub+zip",
        "application/x-mobipocket-ebook",
        "application/vnd.amazon.ebook",
        # Текстовые файлы
        "text/plain",
        "text/markdown",
    }

    def __init__(self, minio_client: Minio) -> None:
        """Инициализация сервиса"""
        self.client = minio_client
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.endpoint = f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}"

        # Создаем бакет, если он не существует
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Проверка существования бакета и его создание при необходимости"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise RuntimeError(f"Failed to create bucket: {str(e)}")

    def _get_content_type(self, file_name: str) -> str:
        """Определение типа контента по имени файла"""
        content_type, _ = mimetypes.guess_type(file_name)
        if content_type is None:
            raise ValueError("Could not determine content type")
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValueError("Invalid content type")
        return content_type

    def _get_object_name(
        self,
        entity_type: str,
        entity_id: UUID,
        file_name: str,
    ) -> str:
        """Формирование имени объекта"""
        return f"{entity_type}/{entity_id}/{file_name}"

    def _get_file_url(self, object_name: str) -> str:
        """Формирование URL файла"""
        return urljoin(
            self.endpoint,
            f"/{self.bucket_name}/{object_name}",
        )

    def _get_object_name_from_url(self, url: str) -> str:
        """Получение имени объекта из URL"""
        parsed = urlparse(url)
        path = parsed.path.lstrip("/")
        parts = path.split("/")
        if len(parts) < 2 or parts[0] != self.bucket_name:
            raise ValueError("Invalid file URL")
        return "/".join(parts[1:])

    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        content_type: str,
        entity_type: str,
        entity_id: UUID,
    ) -> str:
        """Загрузка файла"""
        try:
            # Проверяем размер файла
            file_data = file.read()
            if len(file_data) == 0:
                raise ValueError("Empty file")
            if len(file_data) > self.MAX_FILE_SIZE:
                raise ValueError("File too large")

            # Проверяем тип контента
            if content_type not in self.ALLOWED_CONTENT_TYPES:
                raise ValueError("Invalid content type")

            # Формируем имя объекта
            object_name = self._get_object_name(entity_type, entity_id, file_name)

            # Загружаем файл
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=BytesIO(file_data),
                length=len(file_data),
                content_type=content_type,
            )

            # Возвращаем URL файла
            return self._get_file_url(object_name)

        except S3Error as e:
            raise RuntimeError(f"Failed to upload file: {str(e)}")

    async def delete_file(self, file_url: str) -> None:
        """Удаление файла"""
        try:
            object_name = self._get_object_name_from_url(file_url)
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            raise RuntimeError(f"Failed to delete file: {str(e)}")

    async def get_file_info(self, file_url: str) -> Optional[FileInfo]:
        """Получение информации о файле"""
        try:
            object_name = self._get_object_name_from_url(file_url)
            stat = self.client.stat_object(self.bucket_name, object_name)
            return MinioFileInfo(
                content_type=stat.content_type,
                size=stat.size,
            )
        except S3Error:
            return None

    async def get_file_url(self, file_url: str, expires: int = 3600) -> str:
        """Получение временного URL для доступа к файлу"""
        try:
            object_name = self._get_object_name_from_url(file_url)
            return self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires,
            )
        except S3Error as e:
            raise RuntimeError(f"Failed to get file URL: {str(e)}")

    async def copy_file(
        self,
        source_url: str,
        entity_type: str,
        entity_id: UUID,
        file_name: str,
    ) -> str:
        """Копирование файла"""
        try:
            source_object = self._get_object_name_from_url(source_url)
            target_object = self._get_object_name(entity_type, entity_id, file_name)

            self.client.copy_object(
                bucket_name=self.bucket_name,
                object_name=target_object,
                source_bucket=self.bucket_name,
                source_object=source_object,
            )

            return self._get_file_url(target_object)

        except S3Error as e:
            raise RuntimeError(f"Failed to copy file: {str(e)}")

    async def move_file(
        self,
        source_url: str,
        entity_type: str,
        entity_id: UUID,
        file_name: str,
    ) -> str:
        """Перемещение файла"""
        try:
            # Копируем файл
            new_url = await self.copy_file(
                source_url=source_url,
                entity_type=entity_type,
                entity_id=entity_id,
                file_name=file_name,
            )

            # Удаляем исходный файл
            await self.delete_file(source_url)

            return new_url

        except (S3Error, RuntimeError) as e:
            raise RuntimeError(f"Failed to move file: {str(e)}") 