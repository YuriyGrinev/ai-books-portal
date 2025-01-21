from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from ...entities.user import Comment, User, UserRole
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository interface"""
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    async def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 20) -> List[User]:
        """Get users by role"""
        pass
    
    @abstractmethod
    async def block_user(self, user_id: UUID) -> bool:
        """Block user"""
        pass
    
    @abstractmethod
    async def unblock_user(self, user_id: UUID) -> bool:
        """Unblock user"""
        pass
    
    @abstractmethod
    async def change_role(self, user_id: UUID, new_role: UserRole) -> Optional[User]:
        """Change user role"""
        pass


class CommentRepository(BaseRepository[Comment]):
    """Comment repository interface"""
    
    @abstractmethod
    async def get_by_book(self, book_id: UUID, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get comments by book ID"""
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get comments by user ID"""
        pass
    
    @abstractmethod
    async def get_replies(self, comment_id: UUID, skip: int = 0, limit: int = 20) -> List[Comment]:
        """Get replies to comment"""
        pass
    
    @abstractmethod
    async def soft_delete(self, comment_id: UUID) -> bool:
        """Soft delete comment"""
        pass 