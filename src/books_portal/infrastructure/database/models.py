from datetime import date, datetime
from typing import List
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...domain.entities.base import BaseModel
from ...domain.entities.user import UserRole

# Таблица для связи many-to-many между книгами и авторами
books_authors = Table(
    "books_authors",
    BaseModel.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("author_id", ForeignKey("authors.id"), primary_key=True),
)


class Book(BaseModel):
    """Book model"""
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    isbn: Mapped[str] = mapped_column(String(13), nullable=False, unique=True, index=True)
    publication_date: Mapped[date] = mapped_column(Date, nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cover_url: Mapped[str] = mapped_column(String(255), nullable=True)
    file_url: Mapped[str] = mapped_column(String(255), nullable=True)

    publisher_id: Mapped[UUID] = mapped_column(ForeignKey("publishers.id"), nullable=False)
    publisher: Mapped["Publisher"] = relationship(back_populates="books")
    authors: Mapped[List["Author"]] = relationship(
        secondary=books_authors,
        back_populates="books"
    )
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan"
    )


class Author(BaseModel):
    """Author model"""
    __tablename__ = "authors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    biography: Mapped[str] = mapped_column(Text, nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=True)
    death_date: Mapped[date] = mapped_column(Date, nullable=True)
    photo_url: Mapped[str] = mapped_column(String(255), nullable=True)

    books: Mapped[List["Book"]] = relationship(
        secondary=books_authors,
        back_populates="authors"
    )


class Publisher(BaseModel):
    """Publisher model"""
    __tablename__ = "publishers"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    website: Mapped[str] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str] = mapped_column(String(255), nullable=True)

    books: Mapped[List["Book"]] = relationship(
        back_populates="publisher",
        cascade="all, delete-orphan"
    )


class User(BaseModel):
    """User model"""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avatar_url: Mapped[str] = mapped_column(String(255), nullable=True)

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Comment(BaseModel):
    """Comment model"""
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="comments")

    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id"), nullable=False)
    book: Mapped["Book"] = relationship(back_populates="comments")

    parent_id: Mapped[UUID] = mapped_column(ForeignKey("comments.id"), nullable=True)
    replies: Mapped[List["Comment"]] = relationship(
        back_populates="parent",
        remote_side=[id],
        cascade="all, delete-orphan"
    )
    parent: Mapped["Comment"] = relationship(back_populates="replies", remote_side=[parent_id]) 