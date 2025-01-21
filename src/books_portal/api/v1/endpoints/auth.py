from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import UserRole
from ....domain.ports.services.auth import AuthService
from ....infrastructure.adapters.auth.jwt import JWTAuthService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.user import SQLUserRepository
from ..schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(lambda: JWTAuthService()),
) -> UUID:
    """Получение текущего пользователя"""
    user_id = await auth_service.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(lambda: JWTAuthService()),
) -> TokenResponse:
    """Регистрация нового пользователя"""
    user_repo = SQLUserRepository(session)

    # Проверяем, что пользователь с таким email не существует
    if await user_repo.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Проверяем, что пользователь с таким username не существует
    if await user_repo.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Создаем нового пользователя
    hashed_password = auth_service.hash_password(request.password)
    user = await user_repo.create(
        email=request.email,
        username=request.username,
        hashed_password=hashed_password,
        role=UserRole.USER,
    )

    # Генерируем токены
    access_token = await auth_service.create_access_token(user.id)
    refresh_token = await auth_service.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(lambda: JWTAuthService()),
) -> TokenResponse:
    """Вход в систему"""
    user_repo = SQLUserRepository(session)

    # Получаем пользователя по email
    user = await user_repo.get_by_email(request.username)  # username это email в форме
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем пароль
    if not auth_service.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем, что пользователь активен и не заблокирован
    if not user.is_active or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or blocked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерируем токены
    access_token = await auth_service.create_access_token(user.id)
    refresh_token = await auth_service.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(lambda: JWTAuthService()),
) -> TokenResponse:
    """Обновление токена доступа"""
    user_id = await auth_service.verify_token(request.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерируем новые токены
    access_token = await auth_service.create_access_token(user_id)
    refresh_token = await auth_service.create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    request: PasswordResetRequest,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Запрос на сброс пароля"""
    user_repo = SQLUserRepository(session)

    # Проверяем, что пользователь существует
    user = await user_repo.get_by_email(request.email)
    if not user:
        # Возвращаем 202 даже если пользователь не найден для безопасности
        return

    # TODO: Реализовать отправку email со ссылкой для сброса пароля


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirmRequest,
    session: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(lambda: JWTAuthService()),
) -> None:
    """Подтверждение сброса пароля"""
    # TODO: Реализовать проверку токена и смену пароля


@router.post("/password-change")
async def change_password(
    request: ChangePasswordRequest,
    current_user_id: Annotated[UUID, Depends(get_current_user)],
    session: AsyncSession = Depends(get_async_session),
    auth_service: AuthService = Depends(lambda: JWTAuthService()),
) -> None:
    """Изменение пароля"""
    user_repo = SQLUserRepository(session)

    # Получаем пользователя
    user = await user_repo.get(current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Проверяем старый пароль
    if not auth_service.verify_password(request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password",
        )

    # Обновляем пароль
    hashed_password = auth_service.hash_password(request.new_password)
    await user_repo.update(current_user_id, {"hashed_password": hashed_password}) 