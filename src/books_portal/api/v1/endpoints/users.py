from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import UserRole
from ....domain.ports.services.storage import StorageService
from ....infrastructure.adapters.storage.minio import MinioStorageService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.user import SQLUserRepository
from ..dependencies.auth import check_role, get_current_user_with_data
from ..schemas.users import (
    UserDetailResponse,
    UserResponse,
    UserSearchParams,
    UserUpdate,
)

router = APIRouter()


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_info(
    current_user: Annotated[UserDetailResponse, Depends(get_current_user_with_data)],
) -> UserDetailResponse:
    """Получение информации о текущем пользователе"""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user: UserUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_with_data)],
    session: AsyncSession = Depends(get_async_session),
) -> UserResponse:
    """Обновление информации о текущем пользователе"""
    user_repo = SQLUserRepository(session)

    # Если меняется email, проверяем, что новый email не занят
    if user.email:
        existing_user = await user_repo.get_by_email(user.email)
        if existing_user and existing_user.id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Если меняется username, проверяем, что новый username не занят
    if user.username:
        existing_user = await user_repo.get_by_username(user.username)
        if existing_user and existing_user.id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    # Обновляем пользователя
    return await user_repo.update(current_user_id, user.model_dump(exclude_unset=True))


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    current_user_id: Annotated[UUID, Depends(get_current_user_with_data)],
    session: AsyncSession = Depends(get_async_session),
    storage: StorageService = Depends(lambda: MinioStorageService()),
    file: UploadFile = File(...),
) -> UserResponse:
    """Загрузка аватара пользователя"""
    user_repo = SQLUserRepository(session)

    # Загружаем файл
    avatar_url = await storage.upload_file(
        file=file.file,
        file_name=f"{current_user_id}.{file.filename.split('.')[-1]}",
        content_type=file.content_type,
        entity_type="avatars",
        entity_id=current_user_id,
    )

    # Обновляем URL аватара
    return await user_repo.update(current_user_id, {"avatar_url": str(avatar_url)})


@router.get("", response_model=List[UserResponse])
async def search_users(
    params: Annotated[UserSearchParams, Depends()],
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.ADMIN)),
) -> List[UserResponse]:
    """Поиск пользователей (только для администраторов)"""
    user_repo = SQLUserRepository(session)
    return await user_repo.search(**params.model_dump())


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.ADMIN)),
) -> UserDetailResponse:
    """Получение информации о пользователе (только для администраторов)"""
    user_repo = SQLUserRepository(session)
    user = await user_repo.get_with_stats(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: UUID,
    role: UserRole,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.ADMIN)),
) -> UserResponse:
    """Изменение роли пользователя (только для администраторов)"""
    user_repo = SQLUserRepository(session)

    # Проверяем, что пользователь существует
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Обновляем роль
    return await user_repo.update(user_id, {"role": role})


@router.patch("/{user_id}/block", response_model=UserResponse)
async def block_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.ADMIN)),
) -> UserResponse:
    """Блокировка пользователя (только для администраторов)"""
    user_repo = SQLUserRepository(session)

    # Проверяем, что пользователь существует
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Блокируем пользователя
    return await user_repo.update(user_id, {"is_blocked": True})


@router.patch("/{user_id}/unblock", response_model=UserResponse)
async def unblock_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.ADMIN)),
) -> UserResponse:
    """Разблокировка пользователя (только для администраторов)"""
    user_repo = SQLUserRepository(session)

    # Проверяем, что пользователь существует
    user = await user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Разблокируем пользователя
    return await user_repo.update(user_id, {"is_blocked": False}) 