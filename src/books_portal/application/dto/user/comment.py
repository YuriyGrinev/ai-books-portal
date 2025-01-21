from typing import Optional
from uuid import UUID

from pydantic import field_validator

from ..common.base import BaseDTO, BaseResponseDTO


class CommentCreateDTO(BaseDTO):
    """DTO for creating a comment"""
    content: str
    book_id: UUID
    parent_id: Optional[UUID] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v.strip()) < 1:
            raise ValueError("Комментарий не может быть пустым")
        if len(v) > 1000:
            raise ValueError("Комментарий не может быть длиннее 1000 символов")
        return v.strip()


class CommentUpdateDTO(BaseDTO):
    """DTO for updating a comment"""
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if len(v.strip()) < 1:
            raise ValueError("Комментарий не может быть пустым")
        if len(v) > 1000:
            raise ValueError("Комментарий не может быть длиннее 1000 символов")
        return v.strip()


class CommentResponseDTO(BaseResponseDTO):
    """DTO for comment response"""
    content: str
    user_id: UUID
    book_id: UUID
    parent_id: Optional[UUID] = None
    is_deleted: bool = False


class CommentSearchParams(BaseDTO):
    """DTO for comment search parameters"""
    book_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 20 