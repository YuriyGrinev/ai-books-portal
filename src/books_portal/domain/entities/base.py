from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String, func


class Entity(PydanticBaseModel):
    """Base class for all domain entities"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = uuid4()
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        String(36),
        primary_key=True,
        default=uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    ) 