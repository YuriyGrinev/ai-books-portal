from typing import Protocol

from ...domain.ports.repositories.book import AuthorRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.book.author import AuthorCreateDTO, AuthorResponseDTO


class CreateAuthorDependencies(Protocol):
    """Dependencies for CreateAuthor use case"""
    author_repository: AuthorRepository
    cache_service: CacheService


class CreateAuthor(UseCase[AuthorCreateDTO, AuthorResponseDTO]):
    """Use case for creating an author"""

    def __init__(self, deps: CreateAuthorDependencies):
        self.author_repository = deps.author_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_dto: AuthorCreateDTO) -> AuthorResponseDTO:
        # Создаем автора
        author = await self.author_repository.create(input_dto)

        # Очищаем кэш списка авторов
        await self.cache_service.delete("authors_list")

        return AuthorResponseDTO.model_validate(author) 