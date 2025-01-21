from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from books_portal.domain.entities.user import UserRole
from books_portal.infrastructure.repositories.user import SQLUserRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def admin_token(
    client: AsyncClient,
    session: AsyncSession,
) -> str:
    """Фикстура для получения токена администратора"""
    user_repo = SQLUserRepository(session)
    admin = await user_repo.create(
        email="admin@test.com",
        username="admin",
        hashed_password="hashed",
        role=UserRole.ADMIN,
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
async def user_token(
    client: AsyncClient,
    session: AsyncSession,
) -> tuple[str, UUID]:
    """Фикстура для получения токена пользователя и его ID"""
    user_repo = SQLUserRepository(session)
    user = await user_repo.create(
        email="user@test.com",
        username="user",
        hashed_password="hashed",
        role=UserRole.USER,
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "password"},
    )
    return response.json()["access_token"], user.id


async def test_get_current_user_info(
    client: AsyncClient,
    user_token: tuple[str, UUID],
) -> None:
    """Тест получения информации о текущем пользователе"""
    token, user_id = user_token
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user_id)
    assert data["role"] == UserRole.USER.value
    assert "comments_count" in data


async def test_update_current_user(
    client: AsyncClient,
    user_token: tuple[str, UUID],
) -> None:
    """Тест обновления информации о текущем пользователе"""
    token, user_id = user_token
    update_data = {
        "username": "updated_user",
        "email": "updated@test.com",
    }
    response = await client.patch(
        "/api/v1/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]


async def test_update_current_user_with_existing_email(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    session: AsyncSession,
) -> None:
    """Тест обновления информации о текущем пользователе с существующим email"""
    token, user_id = user_token
    user_repo = SQLUserRepository(session)
    await user_repo.create(
        email="existing@test.com",
        username="existing",
        hashed_password="hashed",
        role=UserRole.USER,
    )

    update_data = {"email": "existing@test.com"}
    response = await client.patch(
        "/api/v1/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


async def test_update_current_user_with_existing_username(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    session: AsyncSession,
) -> None:
    """Тест обновления информации о текущем пользователе с существующим username"""
    token, user_id = user_token
    user_repo = SQLUserRepository(session)
    await user_repo.create(
        email="another@test.com",
        username="existing",
        hashed_password="hashed",
        role=UserRole.USER,
    )

    update_data = {"username": "existing"}
    response = await client.patch(
        "/api/v1/users/me",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]


async def test_search_users_as_admin(
    client: AsyncClient,
    admin_token: str,
    user_token: tuple[str, UUID],
) -> None:
    """Тест поиска пользователей с правами администратора"""
    response = await client.get(
        "/api/v1/users",
        params={"query": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["username"] == "user"


async def test_search_users_as_user(
    client: AsyncClient,
    user_token: tuple[str, UUID],
) -> None:
    """Тест поиска пользователей без прав администратора"""
    token, _ = user_token
    response = await client.get(
        "/api/v1/users",
        params={"query": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_get_user_as_admin(
    client: AsyncClient,
    admin_token: str,
    user_token: tuple[str, UUID],
) -> None:
    """Тест получения информации о пользователе с правами администратора"""
    _, user_id = user_token
    response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user_id)
    assert "comments_count" in data


async def test_get_user_as_user(
    client: AsyncClient,
    user_token: tuple[str, UUID],
) -> None:
    """Тест получения информации о пользователе без прав администратора"""
    token, user_id = user_token
    response = await client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_change_user_role_as_admin(
    client: AsyncClient,
    admin_token: str,
    user_token: tuple[str, UUID],
) -> None:
    """Тест изменения роли пользователя с правами администратора"""
    _, user_id = user_token
    response = await client.patch(
        f"/api/v1/users/{user_id}/role",
        params={"role": UserRole.EDITOR.value},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == UserRole.EDITOR.value


async def test_change_user_role_as_user(
    client: AsyncClient,
    user_token: tuple[str, UUID],
) -> None:
    """Тест изменения роли пользователя без прав администратора"""
    token, user_id = user_token
    response = await client.patch(
        f"/api/v1/users/{user_id}/role",
        params={"role": UserRole.EDITOR.value},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_block_user_as_admin(
    client: AsyncClient,
    admin_token: str,
    user_token: tuple[str, UUID],
) -> None:
    """Тест блокировки пользователя с правами администратора"""
    _, user_id = user_token
    response = await client.patch(
        f"/api/v1/users/{user_id}/block",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_blocked"]


async def test_block_user_as_user(
    client: AsyncClient,
    user_token: tuple[str, UUID],
) -> None:
    """Тест блокировки пользователя без прав администратора"""
    token, user_id = user_token
    response = await client.patch(
        f"/api/v1/users/{user_id}/block",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_unblock_user_as_admin(
    client: AsyncClient,
    admin_token: str,
    user_token: tuple[str, UUID],
    session: AsyncSession,
) -> None:
    """Тест разблокировки пользователя с правами администратора"""
    _, user_id = user_token
    user_repo = SQLUserRepository(session)
    await user_repo.update(user_id, {"is_blocked": True})

    response = await client.patch(
        f"/api/v1/users/{user_id}/unblock",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert not data["is_blocked"]


async def test_unblock_user_as_user(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    session: AsyncSession,
) -> None:
    """Тест разблокировки пользователя без прав администратора"""
    token, user_id = user_token
    user_repo = SQLUserRepository(session)
    await user_repo.update(user_id, {"is_blocked": True})

    response = await client.patch(
        f"/api/v1/users/{user_id}/unblock",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403 