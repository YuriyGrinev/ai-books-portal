from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .....domain.entities.user import Comment, User, UserRole
from .....domain.ports.repositories.user import CommentRepository, UserRepository
from ..models.user import Comment as CommentModel
from ..models.user import User as UserModel
from .base import BaseRepository


class SQLUserRepository(BaseRepository[UserModel, User], UserRepository):
    """SQLAlchemy implementation of UserRepository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(self.model).where(self.model.email == email)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity.model_validate(db_obj)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(self.model).where(self.model.username == username)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity.model_validate(db_obj)

    async def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 20) -> List[User]:
        """Get users by role"""
        stmt = (
            select(self.model)
            .where(self.model.role == role)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def block_user(self, user_id: UUID) -> bool:
        """Block user"""
        stmt = select(self.model).where(self.model.id == user_id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return False

        db_obj.is_blocked = True
        await self.session.flush()
        return True

    async def unblock_user(self, user_id: UUID) -> bool:
        """Unblock user"""
        stmt = select(self.model).where(self.model.id == user_id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return False

        db_obj.is_blocked = False
        await self.session.flush()
        return True

    async def change_role(self, user_id: UUID, new_role: UserRole) -> Optional[User]:
        """Change user role"""
        stmt = select(self.model).where(self.model.id == user_id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None

        db_obj.role = new_role
        await self.session.flush()
        await self.session.refresh(db_obj)
        return self.entity.model_validate(db_obj)


class SQLCommentRepository(BaseRepository[CommentModel, Comment], CommentRepository):
    """SQLAlchemy implementation of CommentRepository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CommentModel, Comment)

    async def get_by_book(self, book_id: UUID, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get comments by book ID"""
        stmt = (
            select(self.model)
            .where(self.model.book_id == book_id)
            .options(
                joinedload(self.model.user),
                selectinload(self.model.replies)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get comments by user ID"""
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .options(
                joinedload(self.model.book),
                selectinload(self.model.replies)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def get_replies(self, comment_id: UUID, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get replies to comment"""
        stmt = (
            select(self.model)
            .where(self.model.parent_id == comment_id)
            .options(
                joinedload(self.model.user),
                joinedload(self.model.book)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def soft_delete(self, comment_id: UUID) -> bool:
        """Soft delete comment"""
        stmt = select(self.model).where(self.model.id == comment_id)
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return False

        db_obj.is_deleted = True
        await self.session.flush()
        return True 