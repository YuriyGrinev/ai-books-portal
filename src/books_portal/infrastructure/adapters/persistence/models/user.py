from typing import List
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ....domain.entities.user import UserRole
from .base import BaseModel


class User(BaseModel):
    """User model"""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Отношения
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="user",
        cascade="all, delete"
    )


class Comment(BaseModel):
    """Comment model"""
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(String, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Отношения
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="comments")
    
    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"))
    book: Mapped["Book"] = relationship(back_populates="comments")
    
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    replies: Mapped[List["Comment"]] = relationship(
        back_populates="parent",
        remote_side=[id],
        cascade="all, delete"
    )
    parent: Mapped["Comment | None"] = relationship(
        back_populates="replies",
        remote_side=[parent_id]
    ) 