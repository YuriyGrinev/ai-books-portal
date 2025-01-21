from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class UserInfo(BaseModel):
    """Краткая информация о пользователе"""
    id: UUID
    username: str
    avatar_url: Optional[HttpUrl] = None


class CommentBase(BaseModel):
    """Базовая схема комментария"""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    """Схема создания комментария"""
    book_id: UUID
    parent_id: Optional[UUID] = None


class CommentUpdate(BaseModel):
    """Схема обновления комментария"""
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(CommentBase):
    """Схема ответа с информацией о комментарии"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_deleted: bool
    user: UserInfo
    parent_id: Optional[UUID] = None
    replies_count: int = 0


class CommentDetailResponse(CommentResponse):
    """Схема ответа с детальной информацией о комментарии"""
    replies: List["CommentDetailResponse"]


class CommentSearchParams(BaseModel):
    """Параметры поиска комментариев"""
    book_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, gt=0, le=100) 