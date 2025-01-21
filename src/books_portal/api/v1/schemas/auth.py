from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """Схема ответа с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Схема запроса на вход"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=32)


class RegisterRequest(BaseModel):
    """Схема запроса на регистрацию"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=32)


class RefreshTokenRequest(BaseModel):
    """Схема запроса на обновление токена"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Схема запроса на сброс пароля"""
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Схема запроса на подтверждение сброса пароля"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=32)


class ChangePasswordRequest(BaseModel):
    """Схема запроса на изменение пароля"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=32) 