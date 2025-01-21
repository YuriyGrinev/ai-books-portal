from typing import Protocol

from ...domain.ports.repositories.book import AuthorRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.author import AuthorResponseDTO, AuthorSearchParams
from ...dto.common.base import PaginatedResponse


class SearchAuthorsDependencies(Protocol):
    """Dependencies for SearchAuthors use case"""
    author_repository: AuthorRepository
    cache_service: CacheService


class SearchAuthors(UseCase[AuthorSearchParams, PaginatedResponse]):
    """Use case for searching authors"""

    def __init__(self, deps: SearchAuthorsDependencies):
        self.author_repository = deps.author_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_dto: AuthorSearchParams) -> PaginatedResponse:
        # Формируем ключ кэша
        cache_key = f"authors_search:{input_dto.model_dump_json()}"

        # Пробуем получить результаты из кэша
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return PaginatedResponse.model_validate(cached_result)

        # Получаем авторов из репозитория
        authors = await self.author_repository.search_by_name(
            name=input_dto.name,
            skip=input_dto.skip,
            limit=input_dto.limit
        )

        # Преобразуем в DTO
        author_dtos = [AuthorResponseDTO.model_validate(author) for author in authors]

        # Создаем ответ с пагинацией
        total = len(author_dtos)  # В реальном приложении нужно получать общее количество из репозитория
        page = input_dto.skip // input_dto.limit + 1
        total_pages = (total + input_dto.limit - 1) // input_dto.limit

        response = PaginatedResponse(
            total=total,
            items=author_dtos,
            page=page,
            pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        # Кэшируем результат на 5 минут
        await self.cache_service.set(cache_key, response.model_dump(), expire=300)

        return response 