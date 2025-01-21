from typing import Optional

from pydantic import EmailStr, HttpUrl, field_validator

from ...domain.entities.user import UserRole
from ..common.base import BaseDTO, BaseResponseDTO


class UserCreateDTO(BaseDTO):
    """DTO for creating a user"""
    email: EmailStr
    username: str
    password: str
    password_confirm: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Имя пользователя должно содержать минимум 3 символа")
        if not v.isalnum():
            raise ValueError("Имя пользователя должно содержать только буквы и цифры")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.islower() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v

    @field_validator("password_confirm")
    @classmethod
    def validate_password_match(cls, v: str, values: dict) -> str:
        if "password" in values and v != values["password"]:
            raise ValueError("Пароли не совпадают")
        return v


class UserUpdateDTO(BaseDTO):
    """DTO for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    password_confirm: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) < 3:
            raise ValueError("Имя пользователя должно содержать минимум 3 символа")
        if not v.isalnum():
            raise ValueError("Имя пользователя должно содержать только буквы и цифры")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v) < 8:
            raise ValueError("Пароль должен содержать минимум 8 символов")
        if not any(c.isupper() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        if not any(c.islower() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну строчную букву")
        if not any(c.isdigit() for c in v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        return v

    @field_validator("password_confirm")
    @classmethod
    def validate_password_match(cls, v: Optional[str], values: dict) -> Optional[str]:
        if v is None:
            return None
        if "password" in values and v != values["password"]:
            raise ValueError("Пароли не совпадают")
        return v


class UserResponseDTO(BaseResponseDTO):
    """DTO for user response"""
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    is_blocked: bool
    avatar_url: Optional[HttpUrl] = None


class UserSearchParams(BaseDTO):
    """DTO for user search parameters"""
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    skip: int = 0
    limit: int = 20 