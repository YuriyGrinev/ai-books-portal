from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import HttpUrl

from .base import Entity


class Author(Entity):
    """Author entity"""
    name: str
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    photo_url: Optional[HttpUrl] = None


class Publisher(Entity):
    """Publisher entity"""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None


class Book(Entity):
    """Book entity"""
    title: str
    description: Optional[str] = None
    isbn: Optional[str] = None
    publication_date: Optional[date] = None
    language: str = "ru"
    page_count: Optional[int] = None
    cover_url: Optional[HttpUrl] = None
    file_url: Optional[HttpUrl] = None
    
    author_ids: List[UUID]
    publisher_id: UUID 