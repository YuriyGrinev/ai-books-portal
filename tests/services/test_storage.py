from io import BytesIO
from uuid import uuid4

import pytest
from minio import Minio

from books_portal.infrastructure.config.settings import settings
from books_portal.infrastructure.services.storage import MinioStorageService


@pytest.fixture
def minio_client() -> Minio:
    """Фикстура для создания клиента MinIO"""
    return Minio(
        f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
        access_key=settings.MINIO_ROOT_USER,
        secret_key=settings.MINIO_ROOT_PASSWORD,
        secure=settings.MINIO_SECURE,
    )


@pytest.fixture
def storage_service(minio_client: Minio) -> MinioStorageService:
    """Фикстура для создания сервиса хранения файлов"""
    return MinioStorageService(minio_client)


@pytest.fixture
def test_file() -> BytesIO:
    """Фикстура для создания тестового файла"""
    return BytesIO(b"test content")


@pytest.fixture
def test_file_params() -> dict:
    """Фикстура с параметрами тестового файла"""
    return {
        "file_name": "test.txt",
        "content_type": "text/plain",
        "entity_type": "test",
        "entity_id": uuid4(),
    }


async def test_upload_file(
    storage_service: MinioStorageService,
    test_file: BytesIO,
    test_file_params: dict,
) -> None:
    """Тест загрузки файла"""
    url = await storage_service.upload_file(
        file=test_file,
        **test_file_params,
    )
    assert url is not None
    assert test_file_params["file_name"] in str(url)
    assert test_file_params["entity_type"] in str(url)
    assert str(test_file_params["entity_id"]) in str(url)


async def test_upload_file_with_same_name(
    storage_service: MinioStorageService,
    test_file: BytesIO,
    test_file_params: dict,
) -> None:
    """Тест загрузки файла с тем же именем"""
    # Загружаем первый файл
    url1 = await storage_service.upload_file(
        file=test_file,
        **test_file_params,
    )

    # Загружаем второй файл с тем же именем
    url2 = await storage_service.upload_file(
        file=test_file,
        **test_file_params,
    )

    assert url1 != url2
    assert test_file_params["file_name"] in str(url2)


async def test_upload_file_with_invalid_content_type(
    storage_service: MinioStorageService,
    test_file: BytesIO,
    test_file_params: dict,
) -> None:
    """Тест загрузки файла с некорректным типом контента"""
    test_file_params["content_type"] = "invalid"
    with pytest.raises(ValueError, match="Invalid content type"):
        await storage_service.upload_file(
            file=test_file,
            **test_file_params,
        )


async def test_upload_file_with_empty_file(
    storage_service: MinioStorageService,
    test_file_params: dict,
) -> None:
    """Тест загрузки пустого файла"""
    empty_file = BytesIO()
    with pytest.raises(ValueError, match="Empty file"):
        await storage_service.upload_file(
            file=empty_file,
            **test_file_params,
        )


async def test_upload_file_with_large_file(
    storage_service: MinioStorageService,
    test_file_params: dict,
) -> None:
    """Тест загрузки большого файла"""
    # Создаем файл размером больше максимально допустимого
    large_file = BytesIO(b"x" * (storage_service.MAX_FILE_SIZE + 1))
    with pytest.raises(ValueError, match="File too large"):
        await storage_service.upload_file(
            file=large_file,
            **test_file_params,
        )


async def test_delete_file(
    storage_service: MinioStorageService,
    test_file: BytesIO,
    test_file_params: dict,
) -> None:
    """Тест удаления файла"""
    # Загружаем файл
    url = await storage_service.upload_file(
        file=test_file,
        **test_file_params,
    )

    # Удаляем файл
    await storage_service.delete_file(url)

    # Проверяем, что файл удален
    with pytest.raises(Exception):
        await storage_service.get_file_info(url)


async def test_delete_nonexistent_file(
    storage_service: MinioStorageService,
) -> None:
    """Тест удаления несуществующего файла"""
    url = f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}/{settings.MINIO_BUCKET_NAME}/nonexistent.txt"
    with pytest.raises(Exception):
        await storage_service.delete_file(url)


async def test_get_file_info(
    storage_service: MinioStorageService,
    test_file: BytesIO,
    test_file_params: dict,
) -> None:
    """Тест получения информации о файле"""
    # Загружаем файл
    url = await storage_service.upload_file(
        file=test_file,
        **test_file_params,
    )

    # Получаем информацию о файле
    info = await storage_service.get_file_info(url)
    assert info is not None
    assert info.content_type == test_file_params["content_type"]
    assert info.size == len(test_file.getvalue()) 