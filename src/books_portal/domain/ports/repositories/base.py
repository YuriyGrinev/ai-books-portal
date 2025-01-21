from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from ...entities.base import Entity

T = TypeVar("T", bound=Entity)


class BaseRepository(ABC, Generic[T]):
    """Base repository interface"""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def get(self, id: UUID) -> Optional[T]:
        """Get entity by id"""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination"""
        pass
    
    @abstractmethod
    async def update(self, id: UUID, entity: T) -> Optional[T]:
        """Update entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity"""
        pass 