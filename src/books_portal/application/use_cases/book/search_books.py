from typing import List, Protocol

from ...domain.ports.repositories.book import BookRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.book import BookResponseDTO, BookSearchParams
from ...dto.common.base import PaginatedResponse


class SearchBooksDependencies(Protocol):
    """Dependencies for SearchBooks use case"""
    book_repository: BookRepository
    cache_service: CacheService


class SearchBooks(UseCase[BookSearchParams, PaginatedResponse]):
    """Use case for searching books"""

    def __init__(self, deps: SearchBooksDependencies):
        self.book_repository = deps.book_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_dto: BookSearchParams) -> PaginatedResponse:
        # Формируем ключ кэша
        cache_key = f"books_search:{input_dto.model_dump_json()}"

        # Пробуем получить результаты из кэша
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return PaginatedResponse.model_validate(cached_result)

        # Получаем книги из репозитория
        books = await self.book_repository.search(
            query=input_dto.query,
            language=input_dto.language,
            author_ids=input_dto.author_ids,
            publisher_id=input_dto.publisher_id,
            skip=input_dto.skip,
            limit=input_dto.limit
        )

        # Преобразуем в DTO
        book_dtos = [BookResponseDTO.model_validate(book) for book in books]

        # Создаем ответ с пагинацией
        total = len(book_dtos)  # В реальном приложении нужно получать общее количество из репозитория
        page = input_dto.skip // input_dto.limit + 1
        total_pages = (total + input_dto.limit - 1) // input_dto.limit

        response = PaginatedResponse(
            total=total,
            items=book_dtos,
            page=page,
            pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        # Кэшируем результат на 5 минут
        await self.cache_service.set(cache_key, response.model_dump(), expire=300)

        return response 