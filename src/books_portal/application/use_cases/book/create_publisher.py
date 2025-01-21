from typing import Protocol

from ...domain.ports.repositories.book import PublisherRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.publisher import PublisherCreateDTO, PublisherResponseDTO


class CreatePublisherDependencies(Protocol):
    """Dependencies for CreatePublisher use case"""
    publisher_repository: PublisherRepository
    cache_service: CacheService


class CreatePublisher(UseCase[PublisherCreateDTO, PublisherResponseDTO]):
    """Use case for creating a publisher"""

    def __init__(self, deps: CreatePublisherDependencies):
        self.publisher_repository = deps.publisher_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_dto: PublisherCreateDTO) -> PublisherResponseDTO:
        # Создаем издательство
        publisher = await self.publisher_repository.create(input_dto)

        # Очищаем кэш списка издательств
        await self.cache_service.delete("publishers_list")

        return PublisherResponseDTO.model_validate(publisher) 