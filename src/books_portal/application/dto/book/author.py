from datetime import date
from typing import Optional

from pydantic import HttpUrl, field_validator

from ..common.base import BaseDTO, BaseResponseDTO


class AuthorCreateDTO(BaseDTO):
    """DTO for creating an author"""
    name: str
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None

    @field_validator("death_date")
    @classmethod
    def validate_death_date(cls, v: Optional[date], values: dict) -> Optional[date]:
        if v is not None and values.get("birth_date") is not None:
            if v < values["birth_date"]:
                raise ValueError("Дата смерти не может быть раньше даты рождения")
        return v


class AuthorUpdateDTO(AuthorCreateDTO):
    """DTO for updating an author"""
    name: Optional[str] = None


class AuthorResponseDTO(BaseResponseDTO):
    """DTO for author response"""
    name: str
    biography: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    photo_url: Optional[HttpUrl] = None


class AuthorSearchParams(BaseDTO):
    """DTO for author search parameters"""
    name: Optional[str] = None
    skip: int = 0
    limit: int = 20 