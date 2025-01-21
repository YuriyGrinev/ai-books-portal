from datetime import date
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from books_portal.domain.entities.user import UserRole
from books_portal.infrastructure.repositories.author import SQLAuthorRepository
from books_portal.infrastructure.repositories.user import SQLUserRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def editor_token(
    client: AsyncClient,
    session: AsyncSession,
) -> str:
    """Фикстура для получения токена редактора"""
    user_repo = SQLUserRepository(session)
    editor = await user_repo.create(
        email="editor@test.com",
        username="editor",
        hashed_password="hashed",
        role=UserRole.EDITOR,
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "editor@test.com", "password": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
async def user_token(
    client: AsyncClient,
    session: AsyncSession,
) -> str:
    """Фикстура для получения токена обычного пользователя"""
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
    return response.json()["access_token"]


@pytest.fixture
async def author_data() -> dict:
    """Фикстура с тестовыми данными для создания автора"""
    return {
        "name": "Test Author",
        "biography": "Test Biography",
        "birth_date": "1990-01-01",
        "death_date": None,
    }


async def test_create_author_as_editor(
    client: AsyncClient,
    editor_token: str,
    author_data: dict,
) -> None:
    """Тест создания автора с правами редактора"""
    response = await client.post(
        "/api/v1/authors",
        json=author_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == author_data["name"]
    assert data["biography"] == author_data["biography"]
    assert UUID(data["id"])


async def test_create_author_as_user(
    client: AsyncClient,
    user_token: str,
    author_data: dict,
) -> None:
    """Тест создания автора без прав редактора"""
    response = await client.post(
        "/api/v1/authors",
        json=author_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


async def test_search_authors(
    client: AsyncClient,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест поиска авторов"""
    author_repo = SQLAuthorRepository(session)
    await author_repo.create(**author_data)

    response = await client.get("/api/v1/authors", params={"query": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == author_data["name"]


async def test_search_authors_by_birth_year(
    client: AsyncClient,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест поиска авторов по году рождения"""
    author_repo = SQLAuthorRepository(session)
    await author_repo.create(**author_data)

    response = await client.get("/api/v1/authors", params={"birth_year": 1990})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == author_data["name"]


async def test_get_author(
    client: AsyncClient,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест получения информации об авторе"""
    author_repo = SQLAuthorRepository(session)
    author = await author_repo.create(**author_data)

    response = await client.get(f"/api/v1/authors/{author.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == author_data["name"]
    assert data["biography"] == author_data["biography"]
    assert "books" in data


async def test_get_nonexistent_author(
    client: AsyncClient,
) -> None:
    """Тест получения информации о несуществующем авторе"""
    response = await client.get(f"/api/v1/authors/{uuid4()}")
    assert response.status_code == 404


async def test_update_author_as_editor(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест обновления автора с правами редактора"""
    author_repo = SQLAuthorRepository(session)
    author = await author_repo.create(**author_data)

    update_data = {
        "name": "Updated Author",
        "biography": "Updated Biography",
    }
    response = await client.patch(
        f"/api/v1/authors/{author.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["biography"] == update_data["biography"]


async def test_update_author_as_user(
    client: AsyncClient,
    user_token: str,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест обновления автора без прав редактора"""
    author_repo = SQLAuthorRepository(session)
    author = await author_repo.create(**author_data)

    update_data = {"name": "Updated Author"}
    response = await client.patch(
        f"/api/v1/authors/{author.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


async def test_delete_author_as_editor(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест удаления автора с правами редактора"""
    author_repo = SQLAuthorRepository(session)
    author = await author_repo.create(**author_data)

    response = await client.delete(
        f"/api/v1/authors/{author.id}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 204

    # Проверяем, что автор действительно удален
    assert not await author_repo.get(author.id)


async def test_delete_author_as_user(
    client: AsyncClient,
    user_token: str,
    session: AsyncSession,
    author_data: dict,
) -> None:
    """Тест удаления автора без прав редактора"""
    author_repo = SQLAuthorRepository(session)
    author = await author_repo.create(**author_data)

    response = await client.delete(
        f"/api/v1/authors/{author.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403

    # Проверяем, что автор не был удален
    assert await author_repo.get(author.id) 