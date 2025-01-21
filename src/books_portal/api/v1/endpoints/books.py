from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import UserRole
from ....domain.ports.services.storage import StorageService
from ....infrastructure.adapters.storage.minio import MinioStorageService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.book import SQLBookRepository
from ..dependencies.auth import check_role
from ..schemas.books import (
    BookCreate,
    BookResponse,
    BookSearchParams,
    BookUpdate,
)

router = APIRouter()


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> BookResponse:
    """Создание новой книги"""
    book_repo = SQLBookRepository(session)

    # Проверяем, что книга с таким ISBN не существует
    if await book_repo.get_by_isbn(book.isbn):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book with this ISBN already exists",
        )

    # Создаем книгу
    return await book_repo.create(**book.model_dump())


@router.get("", response_model=List[BookResponse])
async def search_books(
    params: Annotated[BookSearchParams, Depends()],
    session: AsyncSession = Depends(get_async_session),
) -> List[BookResponse]:
    """Поиск книг"""
    book_repo = SQLBookRepository(session)
    return await book_repo.search(**params.model_dump())


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> BookResponse:
    """Получение информации о книге"""
    book_repo = SQLBookRepository(session)
    book = await book_repo.get_with_relations(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: UUID,
    book: BookUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> BookResponse:
    """Обновление информации о книге"""
    book_repo = SQLBookRepository(session)

    # Проверяем, что книга существует
    if not await book_repo.get(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    # Если меняется ISBN, проверяем, что новый ISBN не занят
    if book.isbn:
        existing_book = await book_repo.get_by_isbn(book.isbn)
        if existing_book and existing_book.id != book_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book with this ISBN already exists",
            )

    # Обновляем книгу
    return await book_repo.update(book_id, book.model_dump(exclude_unset=True))


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> None:
    """Удаление книги"""
    book_repo = SQLBookRepository(session)

    # Проверяем, что книга существует
    book = await book_repo.get(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    # Удаляем книгу
    await book_repo.delete(book_id)


@router.post("/{book_id}/cover", response_model=BookResponse)
async def upload_cover(
    book_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    storage: StorageService = Depends(lambda: MinioStorageService()),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> BookResponse:
    """Загрузка обложки книги"""
    book_repo = SQLBookRepository(session)

    # Проверяем, что книга существует
    book = await book_repo.get(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    # Загружаем файл
    cover_url = await storage.upload_file(
        file=file.file,
        file_name=f"{book_id}.{file.filename.split('.')[-1]}",
        content_type=file.content_type,
        entity_type="covers",
        entity_id=book_id,
    )

    # Обновляем URL обложки
    return await book_repo.update(book_id, {"cover_url": str(cover_url)})


@router.post("/{book_id}/file", response_model=BookResponse)
async def upload_book_file(
    book_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    storage: StorageService = Depends(lambda: MinioStorageService()),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> BookResponse:
    """Загрузка файла книги"""
    book_repo = SQLBookRepository(session)

    # Проверяем, что книга существует
    book = await book_repo.get(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    # Загружаем файл
    file_url = await storage.upload_file(
        file=file.file,
        file_name=f"{book_id}.{file.filename.split('.')[-1]}",
        content_type=file.content_type,
        entity_type="books",
        entity_id=book_id,
    )

    # Обновляем URL файла
    return await book_repo.update(book_id, {"file_url": str(file_url)}) 