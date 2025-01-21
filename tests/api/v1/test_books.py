from datetime import date
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from books_portal.domain.entities.user import UserRole
from books_portal.infrastructure.repositories.book import SQLBookRepository
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
async def book_data() -> dict:
    """Фикстура с тестовыми данными для создания книги"""
    return {
        "title": "Test Book",
        "description": "Test Description",
        "isbn": "978-3-16-148410-0",
        "publication_date": "2024-01-01",
        "language": "en",
        "page_count": 100,
        "publisher_id": str(uuid4()),
        "author_ids": [str(uuid4()) for _ in range(2)],
    }


async def test_create_book_as_editor(
    client: AsyncClient,
    editor_token: str,
    book_data: dict,
) -> None:
    """Тест создания книги с правами редактора"""
    response = await client.post(
        "/api/v1/books",
        json=book_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["isbn"] == book_data["isbn"]
    assert UUID(data["id"])


async def test_create_book_as_user(
    client: AsyncClient,
    user_token: str,
    book_data: dict,
) -> None:
    """Тест создания книги без прав редактора"""
    response = await client.post(
        "/api/v1/books",
        json=book_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


async def test_create_book_with_existing_isbn(
    client: AsyncClient,
    editor_token: str,
    book_data: dict,
    session: AsyncSession,
) -> None:
    """Тест создания книги с существующим ISBN"""
    book_repo = SQLBookRepository(session)
    await book_repo.create(**book_data)

    response = await client.post(
        "/api/v1/books",
        json=book_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 400
    assert "ISBN already exists" in response.json()["detail"]


async def test_search_books(
    client: AsyncClient,
    session: AsyncSession,
    book_data: dict,
) -> None:
    """Тест поиска книг"""
    book_repo = SQLBookRepository(session)
    await book_repo.create(**book_data)

    response = await client.get("/api/v1/books", params={"query": "Test"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == book_data["title"]


async def test_get_book(
    client: AsyncClient,
    session: AsyncSession,
    book_data: dict,
) -> None:
    """Тест получения информации о книге"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.create(**book_data)

    response = await client.get(f"/api/v1/books/{book.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["isbn"] == book_data["isbn"]


async def test_get_nonexistent_book(
    client: AsyncClient,
) -> None:
    """Тест получения информации о несуществующей книге"""
    response = await client.get(f"/api/v1/books/{uuid4()}")
    assert response.status_code == 404


async def test_update_book_as_editor(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    book_data: dict,
) -> None:
    """Тест обновления книги с правами редактора"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.create(**book_data)

    update_data = {"title": "Updated Title"}
    response = await client.patch(
        f"/api/v1/books/{book.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["isbn"] == book_data["isbn"]


async def test_update_book_as_user(
    client: AsyncClient,
    user_token: str,
    session: AsyncSession,
    book_data: dict,
) -> None:
    """Тест обновления книги без прав редактора"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.create(**book_data)

    update_data = {"title": "Updated Title"}
    response = await client.patch(
        f"/api/v1/books/{book.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


async def test_delete_book_as_editor(
    client: AsyncClient,
    editor_token: str,
    session: AsyncSession,
    book_data: dict,
) -> None:
    """Тест удаления книги с правами редактора"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.create(**book_data)

    response = await client.delete(
        f"/api/v1/books/{book.id}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 204

    # Проверяем, что книга действительно удалена
    assert not await book_repo.get(book.id)


async def test_delete_book_as_user(
    client: AsyncClient,
    user_token: str,
    session: AsyncSession,
    book_data: dict,
) -> None:
    """Тест удаления книги без прав редактора"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.create(**book_data)

    response = await client.delete(
        f"/api/v1/books/{book.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403

    # Проверяем, что книга не была удалена
    assert await book_repo.get(book.id) 