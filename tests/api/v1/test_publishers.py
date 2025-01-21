from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from books_portal.domain.entities.user import UserRole
from books_portal.infrastructure.repositories.publisher import SQLPublisherRepository
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
async def publisher_data() -> dict:
    """Фикстура с тестовыми данными для создания издателя"""
    return {
        "name": "Test Publisher",
        "description": "Test Description",
        "website": "https://test-publisher.com",
    }


async def test_create_publisher_as_editor(
    client: AsyncClient,
    editor_token: str,
    publisher_data: dict,
) -> None:
    """Тест создания издателя с правами редактора"""
    response = await client.post(
        "/api/v1/publishers",
        json=publisher_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == publisher_data["name"]
    assert data["description"] == publisher_data["description"]
    assert UUID(data["id"])


async def test_create_publisher_as_user(
    client: AsyncClient,
    user_token: str,
    publisher_data: dict,
) -> None:
    """Тест создания издателя без прав редактора"""
    response = await client.post(
        "/api/v1/publishers",
        json=publisher_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


async def test_create_publisher_with_existing_name(
    client: AsyncClient,
    editor_token: str,
    publisher_data: dict,
    session: AsyncSession,
) -> None:
    """Тест создания издателя с существующим именем"""
    publisher_repo = SQLPublisherRepository(session)
    await publisher_repo.create(**publisher_data)

    response = await client.post(
        "/api/v1/publishers",
        json=publisher_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


async def test_search_publishers(
    client: AsyncClient,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест поиска издателей"""
    publisher_repo = SQLPublisherRepository(session)
    await publisher_repo.create(**publisher_data)

    response = await client.get("/api/v1/publishers", params={"query": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == publisher_data["name"]


async def test_get_publisher(
    client: AsyncClient,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест получения информации об издателе"""
    publisher_repo = SQLPublisherRepository(session)
    publisher = await publisher_repo.create(**publisher_data)

    response = await client.get(f"/api/v1/publishers/{publisher.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == publisher_data["name"]
    assert data["description"] == publisher_data["description"]
    assert "books" in data


async def test_get_nonexistent_publisher(
    client: AsyncClient,
) -> None:
    """Тест получения информации о несуществующем издателе"""
    response = await client.get(f"/api/v1/publishers/{uuid4()}")
    assert response.status_code == 404


async def test_update_publisher_as_editor(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест обновления издателя с правами редактора"""
    publisher_repo = SQLPublisherRepository(session)
    publisher = await publisher_repo.create(**publisher_data)

    update_data = {
        "name": "Updated Publisher",
        "description": "Updated Description",
    }
    response = await client.patch(
        f"/api/v1/publishers/{publisher.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


async def test_update_publisher_as_user(
    client: AsyncClient,
    user_token: str,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест обновления издателя без прав редактора"""
    publisher_repo = SQLPublisherRepository(session)
    publisher = await publisher_repo.create(**publisher_data)

    update_data = {"name": "Updated Publisher"}
    response = await client.patch(
        f"/api/v1/publishers/{publisher.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


async def test_update_publisher_with_existing_name(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест обновления издателя с существующим именем"""
    publisher_repo = SQLPublisherRepository(session)
    publisher1 = await publisher_repo.create(**publisher_data)
    publisher2 = await publisher_repo.create(
        name="Another Publisher",
        description="Another Description",
    )

    update_data = {"name": publisher1.name}
    response = await client.patch(
        f"/api/v1/publishers/{publisher2.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


async def test_delete_publisher_as_editor(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест удаления издателя с правами редактора"""
    publisher_repo = SQLPublisherRepository(session)
    publisher = await publisher_repo.create(**publisher_data)

    response = await client.delete(
        f"/api/v1/publishers/{publisher.id}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 204

    # Проверяем, что издатель действительно удален
    assert not await publisher_repo.get(publisher.id)


async def test_delete_publisher_as_user(
    client: AsyncClient,
    user_token: str,
    session: AsyncSession,
    publisher_data: dict,
) -> None:
    """Тест удаления издателя без прав редактора"""
    publisher_repo = SQLPublisherRepository(session)
    publisher = await publisher_repo.create(**publisher_data)

    response = await client.delete(
        f"/api/v1/publishers/{publisher.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403

    # Проверяем, что издатель не был удален
    assert await publisher_repo.get(publisher.id) 