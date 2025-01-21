from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import UserRole
from ....domain.ports.services.storage import StorageService
from ....infrastructure.adapters.storage.minio import MinioStorageService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.author import SQLAuthorRepository
from ..dependencies.auth import check_role
from ..schemas.authors import (
    AuthorCreate,
    AuthorDetailResponse,
    AuthorResponse,
    AuthorSearchParams,
    AuthorUpdate,
)

router = APIRouter()


@router.post("", response_model=AuthorResponse, status_code=status.HTTP_201_CREATED)
async def create_author(
    author: AuthorCreate,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> AuthorResponse:
    """Создание нового автора"""
    author_repo = SQLAuthorRepository(session)

    # Создаем автора
    return await author_repo.create(**author.model_dump())


@router.get("", response_model=List[AuthorResponse])
async def search_authors(
    params: Annotated[AuthorSearchParams, Depends()],
    session: AsyncSession = Depends(get_async_session),
) -> List[AuthorResponse]:
    """Поиск авторов"""
    author_repo = SQLAuthorRepository(session)
    return await author_repo.search(**params.model_dump())


@router.get("/{author_id}", response_model=AuthorDetailResponse)
async def get_author(
    author_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> AuthorDetailResponse:
    """Получение информации об авторе"""
    author_repo = SQLAuthorRepository(session)
    author = await author_repo.get_with_books(author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )
    return author


@router.patch("/{author_id}", response_model=AuthorResponse)
async def update_author(
    author_id: UUID,
    author: AuthorUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> AuthorResponse:
    """Обновление информации об авторе"""
    author_repo = SQLAuthorRepository(session)

    # Проверяем, что автор существует
    if not await author_repo.get(author_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    # Обновляем автора
    return await author_repo.update(author_id, author.model_dump(exclude_unset=True))


@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> None:
    """Удаление автора"""
    author_repo = SQLAuthorRepository(session)

    # Проверяем, что автор существует
    author = await author_repo.get(author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    # Удаляем автора
    await author_repo.delete(author_id)


@router.post("/{author_id}/photo", response_model=AuthorResponse)
async def upload_photo(
    author_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    storage: StorageService = Depends(lambda: MinioStorageService()),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> AuthorResponse:
    """Загрузка фотографии автора"""
    author_repo = SQLAuthorRepository(session)

    # Проверяем, что автор существует
    author = await author_repo.get(author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Author not found",
        )

    # Загружаем файл
    photo_url = await storage.upload_file(
        file=file.file,
        file_name=f"{author_id}.{file.filename.split('.')[-1]}",
        content_type=file.content_type,
        entity_type="authors",
        entity_id=author_id,
    )

    # Обновляем URL фотографии
    return await author_repo.update(author_id, {"photo_url": str(photo_url)}) 