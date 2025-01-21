from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    """Base DTO class"""
    model_config = ConfigDict(from_attributes=True)


class BaseResponseDTO(BaseDTO):
    """Base response DTO with common fields"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationParams(BaseDTO):
    """Pagination parameters"""
    skip: int = 0
    limit: int = 20


class PaginatedResponse(BaseDTO):
    """Paginated response wrapper"""
    total: int
    items: list
    page: int
    pages: int
    has_next: bool
    has_prev: bool 