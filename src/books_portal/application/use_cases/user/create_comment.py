from typing import Protocol
from uuid import UUID

from ...domain.ports.repositories.book import BookRepository
from ...domain.ports.repositories.user import CommentRepository, UserRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.user.comment import CommentCreateDTO, CommentResponseDTO


class CreateCommentDependencies(Protocol):
    """Dependencies for CreateComment use case"""
    comment_repository: CommentRepository
    book_repository: BookRepository
    user_repository: UserRepository
    cache_service: CacheService


class CreateComment(UseCase[tuple[UUID, CommentCreateDTO], CommentResponseDTO]):
    """Use case for creating a comment"""

    def __init__(self, deps: CreateCommentDependencies):
        self.comment_repository = deps.comment_repository
        self.book_repository = deps.book_repository
        self.user_repository = deps.user_repository
        self.cache_service = deps.cache_service

    async def execute(self, input_data: tuple[UUID, CommentCreateDTO]) -> CommentResponseDTO:
        user_id, input_dto = input_data

        # Проверяем существование пользователя
        user = await self.user_repository.get(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")

        # Проверяем, не заблокирован ли пользователь
        if user.is_blocked:
            raise ValueError("Заблокированные пользователи не могут оставлять комментарии")

        # Проверяем существование книги
        book = await self.book_repository.get(input_dto.book_id)
        if not book:
            raise ValueError(f"Книга с ID {input_dto.book_id} не найдена")

        # Если это ответ на комментарий, проверяем существование родительского комментария
        if input_dto.parent_id:
            parent_comment = await self.comment_repository.get(input_dto.parent_id)
            if not parent_comment:
                raise ValueError(f"Родительский комментарий с ID {input_dto.parent_id} не найден")
            if parent_comment.book_id != input_dto.book_id:
                raise ValueError("Родительский комментарий относится к другой книге")

        # Создаем комментарий
        comment = await self.comment_repository.create({
            **input_dto.model_dump(),
            "user_id": user_id,
            "is_deleted": False
        })

        # Очищаем кэш комментариев к книге
        await self.cache_service.delete(f"book_comments:{input_dto.book_id}")

        return CommentResponseDTO.model_validate(comment) 