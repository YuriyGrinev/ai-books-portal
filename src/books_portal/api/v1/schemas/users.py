from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from ....domain.entities.user import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")


class UserResponse(UserBase):
    """Схема ответа с информацией о пользователе"""
    id: UUID
    role: UserRole
    is_active: bool
    is_blocked: bool
    avatar_url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserDetailResponse(UserResponse):
    """Схема ответа с детальной информацией о пользователе"""
    comments_count: int = 0


class UserSearchParams(BaseModel):
    """Параметры поиска пользователей"""
    query: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, gt=0, le=100) 