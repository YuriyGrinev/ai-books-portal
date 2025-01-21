from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ...entities.user import User, UserRole


class AuthService(ABC):
    """Authentication service interface"""
    
    @abstractmethod
    async def create_access_token(self, user_id: UUID) -> str:
        """Create access token for user"""
        pass
    
    @abstractmethod
    async def create_refresh_token(self, user_id: UUID) -> str:
        """Create refresh token for user"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[UUID]:
        """Verify token and return user ID if valid"""
        pass
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash password"""
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        pass
    
    @abstractmethod
    async def check_permission(self, user: User, required_role: UserRole) -> bool:
        """Check if user has required role"""
        pass 