from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, HttpUrl

from .base import Entity


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    EDITOR = "editor"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


class User(Entity):
    """User entity"""
    email: str
    username: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_blocked: bool = False
    avatar_url: Optional[str] = None


class Comment(Entity):
    """Comment entity"""
    content: str
    user_id: UUID
    book_id: UUID
    parent_id: Optional[UUID] = None
    is_deleted: bool = False 