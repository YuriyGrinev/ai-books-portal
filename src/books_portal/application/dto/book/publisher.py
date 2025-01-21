from typing import Optional

from pydantic import HttpUrl

from ..common.base import BaseDTO, BaseResponseDTO


class PublisherCreateDTO(BaseDTO):
    """DTO for creating a publisher"""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None


class PublisherUpdateDTO(PublisherCreateDTO):
    """DTO for updating a publisher"""
    name: Optional[str] = None


class PublisherResponseDTO(BaseResponseDTO):
    """DTO for publisher response"""
    name: str
    description: Optional[str] = None
    website: Optional[HttpUrl] = None
    logo_url: Optional[HttpUrl] = None


class PublisherSearchParams(BaseDTO):
    """DTO for publisher search parameters"""
    name: Optional[str] = None
    skip: int = 0
    limit: int = 20 