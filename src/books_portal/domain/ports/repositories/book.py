from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from ...entities.book import Author, Book, Publisher
from .base import BaseRepository


class BookRepository(BaseRepository[Book]):
    """Book repository interface"""
    
    @abstractmethod
    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Get book by ISBN"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        author_ids: Optional[List[UUID]] = None,
        publisher_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Book]:
        """Search books by various criteria"""
        pass


class AuthorRepository(BaseRepository[Author]):
    """Author repository interface"""
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 20) -> List[Author]:
        """Search authors by name"""
        pass
    
    @abstractmethod
    async def get_by_book_id(self, book_id: UUID) -> List[Author]:
        """Get authors by book ID"""
        pass


class PublisherRepository(BaseRepository[Publisher]):
    """Publisher repository interface"""
    
    @abstractmethod
    async def search_by_name(self, name: str, skip: int = 0, limit: int = 20) -> List[Publisher]:
        """Search publishers by name"""
        pass
    
    @abstractmethod
    async def get_books(self, publisher_id: UUID, skip: int = 0, limit: int = 20) -> List[Book]:
        """Get all books by publisher"""
        pass 