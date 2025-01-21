from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from .authors import AuthorResponse
from .publishers import PublisherResponse


class AuthorInfo(BaseModel):
    """Краткая информация об авторе"""
    id: UUID
    name: str
    photo_url: Optional[HttpUrl] = None


class PublisherInfo(BaseModel):
    """Краткая информация об издателе"""
    id: UUID
    name: str
    logo_url: Optional[HttpUrl] = None


class BookBase(BaseModel):
    """Базовая схема книги"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    isbn: str = Field(..., pattern=r"^(?=(?:\D*\d){10}(?:(?:\D*\d){3})?$)[\d-]+$")
    publication_date: date
    language: str = Field(..., min_length=2, max_length=3)
    page_count: int = Field(..., gt=0)


class BookCreate(BookBase):
    """Схема создания книги"""
    publisher_id: UUID
    author_ids: List[UUID] = Field(..., min_items=1)


class BookUpdate(BaseModel):
    """Схема обновления книги"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    isbn: Optional[str] = Field(None, pattern=r"^(?=(?:\D*\d){10}(?:(?:\D*\d){3})?$)[\d-]+$")
    publication_date: Optional[date] = None
    language: Optional[str] = Field(None, min_length=2, max_length=3)
    page_count: Optional[int] = Field(None, gt=0)
    publisher_id: Optional[UUID] = None
    author_ids: Optional[List[UUID]] = Field(None, min_items=1)


class BookResponse(BookBase):
    """Схема ответа с информацией о книге"""
    id: UUID
    cover_url: Optional[HttpUrl] = None
    file_url: Optional[HttpUrl] = None
    publisher: PublisherResponse
    authors: List[AuthorResponse]


class BookSearchParams(BaseModel):
    """Параметры поиска книг"""
    query: Optional[str] = None
    language: Optional[str] = Field(None, min_length=2, max_length=3)
    publisher_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    publication_date_from: Optional[date] = None
    publication_date_to: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, gt=0, le=100) 