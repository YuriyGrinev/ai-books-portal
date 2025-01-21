from typing import Protocol
from uuid import UUID

from ...domain.ports.repositories.book import BookRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.book import BookUpdateDTO, BookResponseDTO


class UpdateBookDependencies(Protocol):
    """Dependencies for UpdateBook use case"""
    book_repository: BookRepository
    cache_service: CacheService


class UpdateBook(UseCase[tuple[UUID, BookUpdateDTO], BookResponseDTO]):
    """Use case for updating a book"""

    def __init__(self, deps: UpdateBookDependencies):
        self.book_repository = deps.book_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_data: tuple[UUID, BookUpdateDTO]) -> BookResponseDTO:
        book_id, input_dto = input_data

        # Проверяем существование книги
        existing_book = await self.book_repository.get(book_id)
        if not existing_book:
            raise ValueError(f"Книга с ID {book_id} не найдена")

        # Проверяем ISBN, если он изменился
        if input_dto.isbn and input_dto.isbn != existing_book.isbn:
            book_with_isbn = await self.book_repository.get_by_isbn(input_dto.isbn)
            if book_with_isbn and book_with_isbn.id != book_id:
                raise ValueError(f"Книга с ISBN {input_dto.isbn} уже существует")

        # Обновляем книгу
        updated_book = await self.book_repository.update(book_id, input_dto)
        if not updated_book:
            raise ValueError(f"Не удалось обновить книгу с ID {book_id}")

        # Очищаем кэш
        await self.cache_service.delete(f"book:{book_id}")
        await self.cache_service.delete("books_list")

        return BookResponseDTO.model_validate(updated_book) 