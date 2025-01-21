from typing import Protocol

from ...domain.ports.repositories.book import PublisherRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.publisher import PublisherResponseDTO, PublisherSearchParams
from ...dto.common.base import PaginatedResponse


class SearchPublishersDependencies(Protocol):
    """Dependencies for SearchPublishers use case"""
    publisher_repository: PublisherRepository
    cache_service: CacheService


class SearchPublishers(UseCase[PublisherSearchParams, PaginatedResponse]):
    """Use case for searching publishers"""

    def __init__(self, deps: SearchPublishersDependencies):
        self.publisher_repository = deps.publisher_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_dto: PublisherSearchParams) -> PaginatedResponse:
        # Формируем ключ кэша
        cache_key = f"publishers_search:{input_dto.model_dump_json()}"

        # Пробуем получить результаты из кэша
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return PaginatedResponse.model_validate(cached_result)

        # Получаем издательства из репозитория
        publishers = await self.publisher_repository.search_by_name(
            name=input_dto.name,
            skip=input_dto.skip,
            limit=input_dto.limit
        )

        # Преобразуем в DTO
        publisher_dtos = [PublisherResponseDTO.model_validate(publisher) for publisher in publishers]

        # Создаем ответ с пагинацией
        total = len(publisher_dtos)  # В реальном приложении нужно получать общее количество из репозитория
        page = input_dto.skip // input_dto.limit + 1
        total_pages = (total + input_dto.limit - 1) // input_dto.limit

        response = PaginatedResponse(
            total=total,
            items=publisher_dtos,
            page=page,
            pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        # Кэшируем результат на 5 минут
        await self.cache_service.set(cache_key, response.model_dump(), expire=300)

        return response 