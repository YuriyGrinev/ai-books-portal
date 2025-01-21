from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import HttpUrl, field_validator

from ..common.base import BaseDTO, BaseResponseDTO


class BookCreateDTO(BaseDTO):
    """DTO for creating a book"""
    title: str
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_date: Optional[date] = None
    language: str = "ru"
    page_count: Optional[int] = None
    author_ids: List[UUID]
    publisher_id: UUID

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Удаляем все не цифровые символы
        isbn = "".join(filter(str.isdigit, v))
        if len(isbn) not in [10, 13]:
            raise ValueError("ISBN должен содержать 10 или 13 цифр")
        return isbn


class BookUpdateDTO(BookCreateDTO):
    """DTO for updating a book"""
    title: Optional[str] = None
    author_ids: Optional[List[UUID]] = None
    publisher_id: Optional[UUID] = None


class BookResponseDTO(BaseResponseDTO):
    """DTO for book response"""
    title: str
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_date: Optional[date] = None
    language: str
    page_count: Optional[int] = None
    cover_url: Optional[HttpUrl] = None
    file_url: Optional[HttpUrl] = None
    author_ids: List[UUID]
    publisher_id: UUID


class BookSearchParams(BaseDTO):
    """DTO for book search parameters"""
    query: Optional[str] = None
    language: Optional[str] = None
    author_ids: Optional[List[UUID]] = None
    publisher_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 20 