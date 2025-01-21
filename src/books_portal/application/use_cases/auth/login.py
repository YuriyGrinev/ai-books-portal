from typing import Protocol

from ...domain.ports.repositories.user import UserRepository
from ...domain.ports.services.auth import AuthService
from ..base import UseCase
from ...dto.user.auth import LoginDTO, TokenResponseDTO


class LoginDependencies(Protocol):
    """Dependencies for Login use case"""
    user_repository: UserRepository
    auth_service: AuthService


class Login(UseCase[LoginDTO, TokenResponseDTO]):
    """Use case for user login"""

    def __init__(self, deps: LoginDependencies):
        self.user_repository = deps.user_repository
        self.auth_service = deps.auth_service

    async def execute(self, input_dto: LoginDTO) -> TokenResponseDTO:
        # Получаем пользователя по email
        user = await self.user_repository.get_by_email(input_dto.email)
        if not user:
            raise ValueError("Неверный email или пароль")

        # Проверяем пароль
        if not self.auth_service.verify_password(input_dto.password, user.hashed_password):
            raise ValueError("Неверный email или пароль")

        # Проверяем статус пользователя
        if not user.is_active:
            raise ValueError("Учетная запись не активирована")
        if user.is_blocked:
            raise ValueError("Учетная запись заблокирована")

        # Создаем токены
        access_token = await self.auth_service.create_access_token(user.id)
        refresh_token = await self.auth_service.create_refresh_token(user.id)

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token
        ) 