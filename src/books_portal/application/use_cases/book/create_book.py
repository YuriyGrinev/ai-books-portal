from typing import Protocol

from ...domain.ports.repositories.book import BookRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.book import BookCreateDTO, BookResponseDTO


class CreateBookDependencies(Protocol):
    """Dependencies for CreateBook use case"""
    book_repository: BookRepository
    cache_service: CacheService


class CreateBook(UseCase[BookCreateDTO, BookResponseDTO]):
    """Use case for creating a book"""

    def __init__(self, deps: CreateBookDependencies):
        self.book_repository = deps.book_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_dto: BookCreateDTO) -> BookResponseDTO:
        # Проверяем, существует ли книга с таким ISBN
        if input_dto.isbn:
            existing_book = await self.book_repository.get_by_isbn(input_dto.isbn)
            if existing_book:
                raise ValueError(f"Книга с ISBN {input_dto.isbn} уже существует")

        # Создаем книгу
        book = await self.book_repository.create(input_dto)

        # Очищаем кэш списка книг
        await self.cache_service.delete("books_list")

        return BookResponseDTO.model_validate(book) 