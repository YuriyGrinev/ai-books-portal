from typing import Protocol
from uuid import UUID

from ...domain.ports.repositories.user import CommentRepository
from ...domain.ports.services.cache import CacheService
from ..base import UseCase
from ...dto.user.comment import CommentResponseDTO


class ModerateCommentDependencies(Protocol):
    """Dependencies for ModerateComment use case"""
    comment_repository: CommentRepository
    cache_service: CacheService


class ModerateComment(UseCase[UUID, CommentResponseDTO]):
    """Use case for moderating a comment (soft delete)"""

    def __init__(self, deps: ModerateCommentDependencies):
        self.comment_repository = deps.comment_repository
        self.cache_service = deps.cache_service

    async def execute(self, comment_id: UUID) -> CommentResponseDTO:
        # Проверяем существование комментария
        comment = await self.comment_repository.get(comment_id)
        if not comment:
            raise ValueError(f"Комментарий с ID {comment_id} не найден")

        # Помечаем комментарий как удаленный
        success = await self.comment_repository.soft_delete(comment_id)
        if not success:
            raise ValueError(f"Не удалось удалить комментарий с ID {comment_id}")

        # Получаем обновленный комментарий
        updated_comment = await self.comment_repository.get(comment_id)
        if not updated_comment:
            raise ValueError(f"Не удалось получить обновленный комментарий с ID {comment_id}")

        # Очищаем кэш комментариев к книге
        await self.cache_service.delete(f"book_comments:{updated_comment.book_id}")

        return CommentResponseDTO.model_validate(updated_comment) 