from typing import Protocol
from uuid import UUID

from ...domain.entities.user import UserRole
from ...domain.ports.repositories.user import UserRepository
from ...domain.ports.services.auth import AuthService
from ..base import UseCase
from ...dto.user.user import UserResponseDTO


class ChangeRoleDependencies(Protocol):
    """Dependencies for ChangeRole use case"""
    user_repository: UserRepository
    auth_service: AuthService


class ChangeRole(UseCase[tuple[UUID, UserRole], UserResponseDTO]):
    """Use case for changing user role"""

    def __init__(self, deps: ChangeRoleDependencies):
        self.user_repository = deps.user_repository
        self.auth_service = deps.auth_service

    async def execute(self, input_data: tuple[UUID, UserRole]) -> UserResponseDTO:
        user_id, new_role = input_data

        # Проверяем существование пользователя
        user = await self.user_repository.get(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")

        # Меняем роль пользователя
        updated_user = await self.user_repository.change_role(user_id, new_role)
        if not updated_user:
            raise ValueError(f"Не удалось изменить роль пользователя с ID {user_id}")

        return UserResponseDTO.model_validate(updated_user) 