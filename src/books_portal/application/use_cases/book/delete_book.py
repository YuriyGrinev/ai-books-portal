from typing import Protocol
from uuid import UUID

from ...domain.ports.repositories.book import BookRepository
from ...domain.ports.services.cache import CacheService
from ...domain.ports.services.storage import StorageService
from ..base import UseCase


class DeleteBookDependencies(Protocol):
    """Dependencies for DeleteBook use case"""
    book_repository: BookRepository
    cache_service: CacheService
    storage_service: StorageService


class DeleteBook(UseCase[UUID, bool]):
    """Use case for deleting a book"""

    def __init__(self, deps: DeleteBookDependencies):
        self.book_repository = deps.book_repository
        self.cache_service = deps.cache_service
        self.storage_service = deps.storage_service

    async def execute(self, book_id: UUID) -> bool:
        # Получаем книгу
        book = await self.book_repository.get(book_id)
        if not book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        # Удаляем файлы из хранилища
        if book.cover_url:
            await self.storage_service.delete_file(book.cover_url)
        if book.file_url:
            await self.storage_service.delete_file(book.file_url)

        # Удаляем книгу
        deleted = await self.book_repository.delete(book_id)
        if not deleted:
            raise ValueError(f"Не удалось удалить книгу с ID {book_id}")

        # Очищаем кэш
        await self.cache_service.delete(f"book:{book_id}")
        await self.cache_service.delete("books_list")

        return True 