from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from .books import BookResponse


class AuthorBase(BaseModel):
    """Базовая схема автора"""
    name: str = Field(..., min_length=1, max_length=255)
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None


class AuthorCreate(AuthorBase):
    """Схема создания автора"""
    pass


class AuthorUpdate(BaseModel):
    """Схема обновления автора"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None


class AuthorResponse(AuthorBase):
    """Схема ответа с информацией об авторе"""
    id: UUID
    photo_url: Optional[HttpUrl] = None


class AuthorDetailResponse(AuthorResponse):
    """Схема ответа с детальной информацией об авторе"""
    books: List[BookResponse]


class AuthorSearchParams(BaseModel):
    """Параметры поиска авторов"""
    query: Optional[str] = None
    birth_year: Optional[int] = Field(None, ge=0, le=9999)
    death_year: Optional[int] = Field(None, ge=0, le=9999)
    skip: int = Field(0, ge=0)
    limit: int = Field(10, gt=0, le=100) 