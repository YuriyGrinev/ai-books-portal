from typing import List

import pytest
from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel

from books_portal.infrastructure.config.settings import settings
from books_portal.infrastructure.services.search import ElasticsearchService


class TestDocument(BaseModel):
    """Тестовый документ для индексации"""
    id: str
    title: str
    content: str
    tags: List[str]


@pytest.fixture
async def es_client() -> AsyncElasticsearch:
    """Фикстура для создания клиента Elasticsearch"""
    client = AsyncElasticsearch(
        hosts=[f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
    )
    yield client
    await client.close()


@pytest.fixture
def search_service(es_client: AsyncElasticsearch) -> ElasticsearchService:
    """Фикстура для создания сервиса поиска"""
    return ElasticsearchService(es_client)


@pytest.fixture
def test_index() -> str:
    """Фикстура с тестовым индексом"""
    return "test_index"


@pytest.fixture
async def test_document() -> TestDocument:
    """Фикстура с тестовым документом"""
    return TestDocument(
        id="1",
        title="Test Title",
        content="Test content with some keywords",
        tags=["test", "example"],
    )


async def test_create_index(
    search_service: ElasticsearchService,
    test_index: str,
) -> None:
    """Тест создания индекса"""
    mapping = {
        "properties": {
            "title": {"type": "text"},
            "content": {"type": "text"},
            "tags": {"type": "keyword"},
        }
    }
    
    # Создаем индекс
    await search_service.create_index(test_index, mapping)
    
    # Проверяем, что индекс существует
    exists = await search_service.index_exists(test_index)
    assert exists


async def test_delete_index(
    search_service: ElasticsearchService,
    test_index: str,
) -> None:
    """Тест удаления индекса"""
    # Создаем индекс
    await search_service.create_index(test_index, {})
    
    # Удаляем индекс
    await search_service.delete_index(test_index)
    
    # Проверяем, что индекс не существует
    exists = await search_service.index_exists(test_index)
    assert not exists


async def test_index_document(
    search_service: ElasticsearchService,
    test_index: str,
    test_document: TestDocument,
) -> None:
    """Тест индексации документа"""
    # Создаем индекс
    await search_service.create_index(test_index, {})
    
    # Индексируем документ
    await search_service.index_document(
        index=test_index,
        document_id=test_document.id,
        document=test_document.model_dump(),
    )
    
    # Получаем документ
    doc = await search_service.get_document(test_index, test_document.id)
    assert doc["_source"]["title"] == test_document.title
    assert doc["_source"]["content"] == test_document.content
    assert doc["_source"]["tags"] == test_document.tags


async def test_search_documents(
    search_service: ElasticsearchService,
    test_index: str,
    test_document: TestDocument,
) -> None:
    """Тест поиска документов"""
    # Создаем индекс и индексируем документ
    await search_service.create_index(test_index, {})
    await search_service.index_document(
        index=test_index,
        document_id=test_document.id,
        document=test_document.model_dump(),
    )
    await search_service.refresh_index(test_index)
    
    # Поиск по заголовку
    results = await search_service.search(
        index=test_index,
        query={
            "match": {
                "title": "Test",
            },
        },
    )
    assert len(results["hits"]["hits"]) == 1
    assert results["hits"]["hits"][0]["_source"]["title"] == test_document.title
    
    # Поиск по контенту
    results = await search_service.search(
        index=test_index,
        query={
            "match": {
                "content": "keywords",
            },
        },
    )
    assert len(results["hits"]["hits"]) == 1
    
    # Поиск по тегам
    results = await search_service.search(
        index=test_index,
        query={
            "term": {
                "tags": "test",
            },
        },
    )
    assert len(results["hits"]["hits"]) == 1


async def test_update_document(
    search_service: ElasticsearchService,
    test_index: str,
    test_document: TestDocument,
) -> None:
    """Тест обновления документа"""
    # Создаем индекс и индексируем документ
    await search_service.create_index(test_index, {})
    await search_service.index_document(
        index=test_index,
        document_id=test_document.id,
        document=test_document.model_dump(),
    )
    
    # Обновляем документ
    updated_data = {"title": "Updated Title"}
    await search_service.update_document(
        index=test_index,
        document_id=test_document.id,
        document=updated_data,
    )
    
    # Получаем обновленный документ
    doc = await search_service.get_document(test_index, test_document.id)
    assert doc["_source"]["title"] == "Updated Title"
    assert doc["_source"]["content"] == test_document.content


async def test_delete_document(
    search_service: ElasticsearchService,
    test_index: str,
    test_document: TestDocument,
) -> None:
    """Тест удаления документа"""
    # Создаем индекс и индексируем документ
    await search_service.create_index(test_index, {})
    await search_service.index_document(
        index=test_index,
        document_id=test_document.id,
        document=test_document.model_dump(),
    )
    
    # Удаляем документ
    await search_service.delete_document(test_index, test_document.id)
    
    # Проверяем, что документ не существует
    with pytest.raises(Exception):
        await search_service.get_document(test_index, test_document.id)


async def test_bulk_index_documents(
    search_service: ElasticsearchService,
    test_index: str,
) -> None:
    """Тест массовой индексации документов"""
    # Создаем индекс
    await search_service.create_index(test_index, {})
    
    # Создаем тестовые документы
    documents = [
        TestDocument(
            id=str(i),
            title=f"Title {i}",
            content=f"Content {i}",
            tags=[f"tag{i}"],
        ).model_dump()
        for i in range(3)
    ]
    
    # Массовая индексация
    await search_service.bulk_index(
        index=test_index,
        documents=documents,
        id_field="id",
    )
    await search_service.refresh_index(test_index)
    
    # Проверяем количество документов
    results = await search_service.search(
        index=test_index,
        query={"match_all": {}},
    )
    assert len(results["hits"]["hits"]) == 3 