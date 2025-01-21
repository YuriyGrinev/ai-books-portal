from enum import Enum
from typing import BinaryIO, Protocol
from uuid import UUID

from pydantic import HttpUrl

from ...domain.ports.repositories.book import BookRepository
from ...domain.ports.services.cache import CacheService
from ...domain.ports.services.storage import StorageService
from ..base import UseCase


class BookFileType(str, Enum):
    """Types of book files"""
    COVER = "cover"
    CONTENT = "content"


class UploadBookFileDependencies(Protocol):
    """Dependencies for UploadBookFile use case"""
    book_repository: BookRepository
    storage_service: StorageService
    cache_service: CacheService


class UploadBookFile(UseCase[tuple[UUID, BookFileType, BinaryIO, str], HttpUrl]):
    """Use case for uploading book files"""

    def __init__(self, deps: UploadBookFileDependencies):
        self.book_repository = deps.book_repository
        self.storage_service = deps.storage_service
        self.cache_service = deps.cache_service

    async def execute(self, input_data: tuple[UUID, BookFileType, BinaryIO, str]) -> HttpUrl:
        book_id, file_type, file, content_type = input_data

        # Проверяем существование книги
        book = await self.book_repository.get(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        # Загружаем файл
        file_url = await self.storage_service.upload_file(
            file=file,
            file_name=f"{book_id}_{file_type.value}",
            content_type=content_type,
            entity_type="book",
            entity_id=book_id
        )

        # Обновляем URL в книге
        if file_type == BookFileType.COVER:
            # Если есть старая обложка, удаляем её
            if book.cover_url:
                await self.storage_service.delete_file(book.cover_url)
            book.cover_url = file_url
        else:  # CONTENT
            # Если есть старый файл, удаляем его
            if book.file_url:
                await self.storage_service.delete_file(book.file_url)
            book.file_url = file_url

        # Сохраняем изменения
        updated_book = await self.book_repository.update(book_id, book)
        if not updated_book:
            # Если не удалось обновить книгу, удаляем загруженный файл
            await self.storage_service.delete_file(file_url)
            raise ValueError(f"Не удалось обновить книгу с ID {book_id}")

        # Очищаем кэш
        await self.cache_service.delete(f"book:{book_id}")

        return file_url 