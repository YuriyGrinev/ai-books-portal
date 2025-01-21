from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from books_portal.domain.entities.user import UserRole
from books_portal.infrastructure.repositories.book import SQLBookRepository
from books_portal.infrastructure.repositories.comment import SQLCommentRepository
from books_portal.infrastructure.repositories.user import SQLUserRepository

pytestmark = pytest.mark.asyncio


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


@pytest.fixture
async def another_user_token(
    client: AsyncClient,
    session: AsyncSession,
) -> tuple[str, UUID]:
    """Фикстура для получения токена другого пользователя и его ID"""
    user_repo = SQLUserRepository(session)
    user = await user_repo.create(
        email="another@test.com",
        username="another",
        hashed_password="hashed",
        role=UserRole.USER,
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "another@test.com", "password": "password"},
    )
    return response.json()["access_token"], user.id


@pytest.fixture
async def moderator_token(
    client: AsyncClient,
    session: AsyncSession,
) -> str:
    """Фикстура для получения токена модератора"""
    user_repo = SQLUserRepository(session)
    moderator = await user_repo.create(
        email="moderator@test.com",
        username="moderator",
        hashed_password="hashed",
        role=UserRole.MODERATOR,
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.com", "password": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
async def book_id(session: AsyncSession) -> UUID:
    """Фикстура для создания книги и получения её ID"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.create(
        title="Test Book",
        description="Test Description",
        isbn="978-3-16-148410-0",
        publication_date="2024-01-01",
        language="en",
        page_count=100,
        publisher_id=uuid4(),
        author_ids=[uuid4() for _ in range(2)],
    )
    return book.id


@pytest.fixture
async def comment_data(book_id: UUID) -> dict:
    """Фикстура с тестовыми данными для создания комментария"""
    return {
        "content": "Test Comment",
        "book_id": str(book_id),
        "parent_id": None,
    }


async def test_create_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
) -> None:
    """Тест создания комментария"""
    token, user_id = user_token
    response = await client.post(
        "/api/v1/comments",
        json=comment_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == comment_data["content"]
    assert data["user"]["id"] == str(user_id)
    assert UUID(data["id"])


async def test_create_reply(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест создания ответа на комментарий"""
    token, user_id = user_token
    comment_repo = SQLCommentRepository(session)
    parent = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=user_id,
    )

    reply_data = {
        **comment_data,
        "parent_id": str(parent.id),
    }
    response = await client.post(
        "/api/v1/comments",
        json=reply_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == str(parent.id)


async def test_create_reply_to_nonexistent_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
) -> None:
    """Тест создания ответа на несуществующий комментарий"""
    token, _ = user_token
    reply_data = {
        **comment_data,
        "parent_id": str(uuid4()),
    }
    response = await client.post(
        "/api/v1/comments",
        json=reply_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


async def test_search_comments(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест поиска комментариев"""
    token, user_id = user_token
    comment_repo = SQLCommentRepository(session)
    await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=user_id,
    )

    response = await client.get(
        "/api/v1/comments",
        params={"book_id": comment_data["book_id"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == comment_data["content"]


async def test_get_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест получения информации о комментарии"""
    token, user_id = user_token
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=user_id,
    )

    response = await client.get(f"/api/v1/comments/{comment.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == comment_data["content"]
    assert "replies" in data


async def test_get_nonexistent_comment(
    client: AsyncClient,
) -> None:
    """Тест получения информации о несуществующем комментарии"""
    response = await client.get(f"/api/v1/comments/{uuid4()}")
    assert response.status_code == 404


async def test_update_own_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест обновления своего комментария"""
    token, user_id = user_token
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=user_id,
    )

    update_data = {"content": "Updated Comment"}
    response = await client.patch(
        f"/api/v1/comments/{comment.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == update_data["content"]


async def test_update_other_user_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    another_user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест обновления чужого комментария"""
    token, _ = user_token
    another_token, another_user_id = another_user_token
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=another_user_id,
    )

    update_data = {"content": "Updated Comment"}
    response = await client.patch(
        f"/api/v1/comments/{comment.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_delete_own_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест удаления своего комментария"""
    token, user_id = user_token
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=user_id,
    )

    response = await client.delete(
        f"/api/v1/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # Проверяем, что комментарий помечен как удаленный
    updated_comment = await comment_repo.get(comment.id)
    assert updated_comment.is_deleted


async def test_delete_other_user_comment_as_moderator(
    client: AsyncClient,
    moderator_token: str,
    user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест удаления чужого комментария модератором"""
    _, user_id = user_token
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=user_id,
    )

    response = await client.delete(
        f"/api/v1/comments/{comment.id}",
        headers={"Authorization": f"Bearer {moderator_token}"},
    )
    assert response.status_code == 204

    # Проверяем, что комментарий помечен как удаленный
    updated_comment = await comment_repo.get(comment.id)
    assert updated_comment.is_deleted


async def test_delete_other_user_comment(
    client: AsyncClient,
    user_token: tuple[str, UUID],
    another_user_token: tuple[str, UUID],
    comment_data: dict,
    session: AsyncSession,
) -> None:
    """Тест удаления чужого комментария обычным пользователем"""
    token, _ = user_token
    another_token, another_user_id = another_user_token
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.create(
        content=comment_data["content"],
        book_id=UUID(comment_data["book_id"]),
        user_id=another_user_id,
    )

    response = await client.delete(
        f"/api/v1/comments/{comment.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

    # Проверяем, что комментарий не был удален
    updated_comment = await comment_repo.get(comment.id)
    assert not updated_comment.is_deleted 