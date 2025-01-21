from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import UserRole
from ....domain.ports.services.storage import StorageService
from ....infrastructure.adapters.storage.minio import MinioStorageService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.publisher import SQLPublisherRepository
from ..dependencies.auth import check_role
from ..schemas.publishers import (
    PublisherCreate,
    PublisherDetailResponse,
    PublisherResponse,
    PublisherSearchParams,
    PublisherUpdate,
)

router = APIRouter()


@router.post("", response_model=PublisherResponse, status_code=status.HTTP_201_CREATED)
async def create_publisher(
    publisher: PublisherCreate,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> PublisherResponse:
    """Создание нового издателя"""
    publisher_repo = SQLPublisherRepository(session)

    # Проверяем, что издатель с таким именем не существует
    if await publisher_repo.get_by_name(publisher.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Publisher with this name already exists",
        )

    # Создаем издателя
    return await publisher_repo.create(**publisher.model_dump())


@router.get("", response_model=List[PublisherResponse])
async def search_publishers(
    params: Annotated[PublisherSearchParams, Depends()],
    session: AsyncSession = Depends(get_async_session),
) -> List[PublisherResponse]:
    """Поиск издателей"""
    publisher_repo = SQLPublisherRepository(session)
    return await publisher_repo.search(**params.model_dump())


@router.get("/{publisher_id}", response_model=PublisherDetailResponse)
async def get_publisher(
    publisher_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> PublisherDetailResponse:
    """Получение информации об издателе"""
    publisher_repo = SQLPublisherRepository(session)
    publisher = await publisher_repo.get_with_books(publisher_id)
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found",
        )
    return publisher


@router.patch("/{publisher_id}", response_model=PublisherResponse)
async def update_publisher(
    publisher_id: UUID,
    publisher: PublisherUpdate,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> PublisherResponse:
    """Обновление информации об издателе"""
    publisher_repo = SQLPublisherRepository(session)

    # Проверяем, что издатель существует
    if not await publisher_repo.get(publisher_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found",
        )

    # Если меняется имя, проверяем, что новое имя не занято
    if publisher.name:
        existing_publisher = await publisher_repo.get_by_name(publisher.name)
        if existing_publisher and existing_publisher.id != publisher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publisher with this name already exists",
            )

    # Обновляем издателя
    return await publisher_repo.update(publisher_id, publisher.model_dump(exclude_unset=True))


@router.delete("/{publisher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_publisher(
    publisher_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> None:
    """Удаление издателя"""
    publisher_repo = SQLPublisherRepository(session)

    # Проверяем, что издатель существует
    publisher = await publisher_repo.get(publisher_id)
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found",
        )

    # Удаляем издателя
    await publisher_repo.delete(publisher_id)


@router.post("/{publisher_id}/logo", response_model=PublisherResponse)
async def upload_logo(
    publisher_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    storage: StorageService = Depends(lambda: MinioStorageService()),
    _: None = Depends(check_role(UserRole.EDITOR)),
) -> PublisherResponse:
    """Загрузка логотипа издателя"""
    publisher_repo = SQLPublisherRepository(session)

    # Проверяем, что издатель существует
    publisher = await publisher_repo.get(publisher_id)
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publisher not found",
        )

    # Загружаем файл
    logo_url = await storage.upload_file(
        file=file.file,
        file_name=f"{publisher_id}.{file.filename.split('.')[-1]}",
        content_type=file.content_type,
        entity_type="publishers",
        entity_id=publisher_id,
    )

    # Обновляем URL логотипа
    return await publisher_repo.update(publisher_id, {"logo_url": str(logo_url)}) 