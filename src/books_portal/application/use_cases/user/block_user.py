from typing import Protocol
from uuid import UUID

from ...domain.ports.repositories.user import UserRepository
from ..base import UseCase
from ...dto.user.user import UserResponseDTO


class BlockUserDependencies(Protocol):
    """Dependencies for BlockUser use case"""
    user_repository: UserRepository


class BlockUser(UseCase[tuple[UUID, bool], UserResponseDTO]):
    """Use case for blocking/unblocking user"""

    def __init__(self, deps: BlockUserDependencies):
        self.user_repository = deps.user_repository

    async def execute(self, input_data: tuple[UUID, bool]) -> UserResponseDTO:
        user_id, block = input_data

        # Проверяем существование пользователя
        user = await self.user_repository.get(user_id)
        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден")

        # Блокируем или разблокируем пользователя
        if block:
            success = await self.user_repository.block_user(user_id)
            if not success:
                raise ValueError(f"Не удалось заблокировать пользователя с ID {user_id}")
        else:
            success = await self.user_repository.unblock_user(user_id)
            if not success:
                raise ValueError(f"Не удалось разблокировать пользователя с ID {user_id}")

        # Получаем обновленного пользователя
        updated_user = await self.user_repository.get(user_id)
        if not updated_user:
            raise ValueError(f"Не удалось получить обновленного пользователя с ID {user_id}")

        return UserResponseDTO.model_validate(updated_user) 