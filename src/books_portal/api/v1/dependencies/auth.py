from typing import Annotated, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import User, UserRole
from ....domain.ports.services.auth import AuthService
from ....infrastructure.adapters.auth.jwt import JWTAuthService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.user import SQLUserRepository
from ..endpoints.auth import get_current_user


async def get_current_user_with_data(
    current_user_id: Annotated[UUID, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Получение данных текущего пользователя"""
    user_repo = SQLUserRepository(session)
    user = await user_repo.get(current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def check_role(required_role: UserRole) -> Callable:
    """Проверка роли пользователя"""
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user_with_data)],
        auth_service: AuthService = Depends(lambda: JWTAuthService()),
    ) -> None:
        if not await auth_service.check_permission(current_user, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    return role_checker


# Готовые зависимости для проверки ролей
require_admin = check_role(UserRole.ADMIN)
require_editor = check_role(UserRole.EDITOR)
require_moderator = check_role(UserRole.MODERATOR)
require_user = check_role(UserRole.USER) 