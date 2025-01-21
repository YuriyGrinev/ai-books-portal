from typing import Optional

from pydantic import EmailStr

from ..common.base import BaseDTO


class LoginDTO(BaseDTO):
    """DTO for user login"""
    email: EmailStr
    password: str


class TokenResponseDTO(BaseDTO):
    """DTO for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayloadDTO(BaseDTO):
    """DTO for token payload"""
    sub: str  # user_id
    exp: int  # expiration time
    type: str  # token type (access or refresh)


class ChangePasswordDTO(BaseDTO):
    """DTO for changing password"""
    current_password: str
    new_password: str
    new_password_confirm: str


class ResetPasswordRequestDTO(BaseDTO):
    """DTO for requesting password reset"""
    email: EmailStr


class ResetPasswordDTO(BaseDTO):
    """DTO for resetting password"""
    token: str
    new_password: str
    new_password_confirm: str


class RefreshTokenDTO(BaseDTO):
    """DTO for refreshing token"""
    refresh_token: str 