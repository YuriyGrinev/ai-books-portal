from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from .books import BookResponse


class PublisherBase(BaseModel):
    """Базовая схема издателя"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    website: Optional[HttpUrl] = None


class PublisherCreate(PublisherBase):
    """Схема создания издателя"""
    pass


class PublisherUpdate(BaseModel):
    """Схема обновления издателя"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    website: Optional[HttpUrl] = None


class PublisherResponse(PublisherBase):
    """Схема ответа с информацией об издателе"""
    id: UUID
    logo_url: Optional[HttpUrl] = None


class PublisherDetailResponse(PublisherResponse):
    """Схема ответа с детальной информацией об издателе"""
    books: List[BookResponse]


class PublisherSearchParams(BaseModel):
    """Параметры поиска издателей"""
    query: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(10, gt=0, le=100) 