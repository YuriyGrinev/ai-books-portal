from datetime import date
from typing import List
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# Таблица для связи многие-ко-многим между книгами и авторами
books_authors = Table(
    "books_authors",
    BaseModel.metadata,
    mapped_column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("author_id", ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)


class Book(BaseModel):
    """Book model"""
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(13), unique=True, nullable=True, index=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="ru")
    page_count: Mapped[int | None] = mapped_column(nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Отношения
    publisher_id: Mapped[UUID] = mapped_column(ForeignKey("publishers.id", ondelete="CASCADE"))
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
    authors: Mapped[List["Author"]] = relationship(
        secondary=books_authors,
        back_populates="books",
        cascade="all, delete"
    )


class Author(BaseModel):
    """Author model"""
    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    biography: Mapped[str | None] = mapped_column(String, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Отношения
    books: Mapped[List["Book"]] = relationship(
        secondary=books_authors,
        back_populates="authors",
        cascade="all, delete"
    )


class Publisher(BaseModel):
    """Publisher model"""
    __tablename__ = "publishers"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    website: Mapped[str | None] = mapped_column(String, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Отношения
    books: Mapped[List["Book"]] = relationship(
        back_populates="publisher",
        cascade="all, delete"
    ) 