from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .....domain.entities.book import Author, Book, Publisher
from .....domain.ports.repositories.book import AuthorRepository, BookRepository, PublisherRepository
from ..models.book import Author as AuthorModel
from ..models.book import Book as BookModel
from ..models.book import Publisher as PublisherModel
from .base import BaseRepository


class SQLBookRepository(BaseRepository[BookModel, Book], BookRepository):
    """SQLAlchemy implementation of BookRepository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, BookModel, Book)

    async def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Get book by ISBN"""
        stmt = (
            select(self.model)
            .where(self.model.isbn == isbn)
            .options(
                joinedload(self.model.publisher),
                selectinload(self.model.authors)
            )
        )
        result = await self.session.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if db_obj is None:
            return None
        return self.entity.model_validate(db_obj)

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
        stmt = select(self.model).options(
            joinedload(self.model.publisher),
            selectinload(self.model.authors)
        )

        if query:
            stmt = stmt.where(self.model.title.ilike(f"%{query}%"))
        if language:
            stmt = stmt.where(self.model.language == language)
        if publisher_id:
            stmt = stmt.where(self.model.publisher_id == publisher_id)
        if author_ids:
            stmt = stmt.join(self.model.authors).where(AuthorModel.id.in_(author_ids))

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]


class SQLAuthorRepository(BaseRepository[AuthorModel, Author], AuthorRepository):
    """SQLAlchemy implementation of AuthorRepository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuthorModel, Author)

    async def search_by_name(self, name: str, skip: int = 0, limit: int = 20) -> List[Author]:
        """Search authors by name"""
        stmt = (
            select(self.model)
            .where(self.model.name.ilike(f"%{name}%"))
            .options(selectinload(self.model.books))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def get_by_book_id(self, book_id: UUID) -> List[Author]:
        """Get authors by book ID"""
        stmt = (
            select(self.model)
            .join(self.model.books)
            .where(BookModel.id == book_id)
            .options(selectinload(self.model.books))
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]


class SQLPublisherRepository(BaseRepository[PublisherModel, Publisher], PublisherRepository):
    """SQLAlchemy implementation of PublisherRepository"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PublisherModel, Publisher)

    async def search_by_name(self, name: str, skip: int = 0, limit: int = 20) -> List[Publisher]:
        """Search publishers by name"""
        stmt = (
            select(self.model)
            .where(self.model.name.ilike(f"%{name}%"))
            .options(selectinload(self.model.books))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [self.entity.model_validate(obj) for obj in result.scalars().all()]

    async def get_books(self, publisher_id: UUID, skip: int = 0, limit: int = 20) -> List[Book]:
        """Get all books by publisher"""
        stmt = (
            select(BookModel)
            .where(BookModel.publisher_id == publisher_id)
            .options(
                joinedload(BookModel.publisher),
                selectinload(BookModel.authors)
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [Book.model_validate(obj) for obj in result.scalars().all()] 