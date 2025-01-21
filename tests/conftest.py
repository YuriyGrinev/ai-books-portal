import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from books_portal.infrastructure.database.base import Base
from books_portal.infrastructure.database.session import get_async_session
from books_portal.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Создает event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_engine() -> AsyncEngine:
    """Создает тестовый движок SQLAlchemy"""
    return create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/books_portal_test",
        echo=True,
    )


@pytest.fixture(autouse=True)
async def setup_database(test_engine: AsyncEngine) -> AsyncGenerator:
    """Создает и очищает таблицы в тестовой базе данных"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Создает сессию SQLAlchemy для тестов"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def test_app(session: AsyncSession) -> FastAPI:
    """Создает тестовое приложение FastAPI"""
    app.dependency_overrides[get_async_session] = lambda: session
    return app


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Создает тестовый клиент FastAPI"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client 