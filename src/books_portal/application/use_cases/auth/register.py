from typing import Protocol

from ...domain.ports.repositories.user import UserRepository
from ...domain.ports.services.auth import AuthService
from ..base import UseCase
from ...dto.user.user import UserCreateDTO, UserResponseDTO


class RegisterDependencies(Protocol):
    """Dependencies for Register use case"""
    user_repository: UserRepository
    auth_service: AuthService


class Register(UseCase[UserCreateDTO, UserResponseDTO]):
    """Use case for user registration"""

    def __init__(self, deps: RegisterDependencies):
        self.user_repository = deps.user_repository
        self.auth_service = deps.auth_service

    async def execute(self, input_dto: UserCreateDTO) -> UserResponseDTO:
        # Проверяем, не занят ли email
        existing_user = await self.user_repository.get_by_email(input_dto.email)
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")

        # Проверяем, не занято ли имя пользователя
        existing_user = await self.user_repository.get_by_username(input_dto.username)
        if existing_user:
            raise ValueError("Пользователь с таким именем уже существует")

        # Хэшируем пароль
        hashed_password = self.auth_service.hash_password(input_dto.password)

        # Создаем пользователя
        user = await self.user_repository.create({
            "email": input_dto.email,
            "username": input_dto.username,
            "hashed_password": hashed_password,
            "is_active": True,  # По умолчанию активируем пользователя
            "is_blocked": False
        })

        return UserResponseDTO.model_validate(user) 