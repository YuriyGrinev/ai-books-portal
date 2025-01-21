from typing import AsyncGenerator
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from books_portal.domain.entities.user import UserRole
from books_portal.infrastructure.repositories.user import SQLUserRepository
from books_portal.infrastructure.services.auth import JWTAuthService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def register_data() -> dict:
    """Фикстура с тестовыми данными для регистрации"""
    return {
        "email": "test@test.com",
        "username": "test_user",
        "password": "test_password",
    }


@pytest.fixture
async def registered_user(
    client: AsyncClient,
    register_data: dict,
) -> dict:
    """Фикстура для создания зарегистрированного пользователя"""
    response = await client.post("/api/v1/auth/register", json=register_data)
    return response.json()


async def test_register_user(
    client: AsyncClient,
    register_data: dict,
) -> None:
    """Тест регистрации пользователя"""
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == register_data["email"]
    assert data["username"] == register_data["username"]
    assert "id" in data
    assert "password" not in data
    assert data["role"] == UserRole.USER.value
    assert data["is_active"]
    assert not data["is_blocked"]


async def test_register_user_with_existing_email(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест регистрации пользователя с существующим email"""
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


async def test_register_user_with_invalid_email(
    client: AsyncClient,
    register_data: dict,
) -> None:
    """Тест регистрации пользователя с некорректным email"""
    register_data["email"] = "invalid_email"
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 422


async def test_register_user_with_invalid_username(
    client: AsyncClient,
    register_data: dict,
) -> None:
    """Тест регистрации пользователя с некорректным username"""
    register_data["username"] = "u"  # слишком короткий
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 422


async def test_login_user(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест входа пользователя"""
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_user_with_wrong_password(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест входа пользователя с неверным паролем"""
    login_data = {
        "email": register_data["email"],
        "password": "wrong_password",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


async def test_login_nonexistent_user(
    client: AsyncClient,
) -> None:
    """Тест входа несуществующего пользователя"""
    login_data = {
        "email": "nonexistent@test.com",
        "password": "password",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


async def test_login_blocked_user(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
    session: AsyncSession,
) -> None:
    """Тест входа заблокированного пользователя"""
    # Блокируем пользователя
    user_repo = SQLUserRepository(session)
    await user_repo.update(
        UUID(registered_user["id"]),
        {"is_blocked": True},
    )

    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 403
    assert "blocked" in response.json()["detail"]


async def test_refresh_token(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест обновления токена"""
    # Сначала логинимся
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    refresh_token = login_response.json()["refresh_token"]

    # Обновляем токен
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_refresh_token_with_invalid_token(
    client: AsyncClient,
) -> None:
    """Тест обновления токена с невалидным токеном"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"},
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


async def test_request_password_reset(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест запроса сброса пароля"""
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": register_data["email"]},
    )
    assert response.status_code == 200


async def test_request_password_reset_nonexistent_user(
    client: AsyncClient,
) -> None:
    """Тест запроса сброса пароля для несуществующего пользователя"""
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nonexistent@test.com"},
    )
    assert response.status_code == 404


async def test_change_password(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест изменения пароля"""
    # Сначала логинимся
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Меняем пароль
    change_data = {
        "old_password": register_data["password"],
        "new_password": "new_password",
    }
    response = await client.post(
        "/api/v1/auth/password/change",
        json=change_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Проверяем, что можем войти с новым паролем
    new_login_data = {
        "email": register_data["email"],
        "password": "new_password",
    }
    new_login_response = await client.post("/api/v1/auth/login", json=new_login_data)
    assert new_login_response.status_code == 200


async def test_change_password_with_wrong_old_password(
    client: AsyncClient,
    register_data: dict,
    registered_user: dict,
) -> None:
    """Тест изменения пароля с неверным старым паролем"""
    # Сначала логинимся
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]

    # Пытаемся сменить пароль с неверным старым паролем
    change_data = {
        "old_password": "wrong_password",
        "new_password": "new_password",
    }
    response = await client.post(
        "/api/v1/auth/password/change",
        json=change_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "Invalid password" in response.json()["detail"] 