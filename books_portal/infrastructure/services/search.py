from typing import Any, Dict, List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError

from books_portal.domain.interfaces.search import SearchService
from books_portal.domain.schemas.books import BookSearchParams
from books_portal.domain.schemas.authors import AuthorSearchParams


class ElasticsearchSearchService(SearchService):
    """Сервис поиска на основе Elasticsearch"""

    # Имена индексов
    BOOKS_INDEX = "books"
    AUTHORS_INDEX = "authors"

    # Маппинги для индексов
    BOOKS_MAPPING = {
        "properties": {
            "id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion", "analyzer": "russian"},
                },
            },
            "description": {"type": "text", "analyzer": "russian"},
            "isbn": {"type": "keyword"},
            "language": {"type": "keyword"},
            "publication_date": {"type": "date"},
            "page_count": {"type": "integer"},
            "publisher_id": {"type": "keyword"},
            "publisher_name": {"type": "keyword"},
            "author_ids": {"type": "keyword"},
            "author_names": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    }

    AUTHORS_MAPPING = {
        "properties": {
            "id": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion", "analyzer": "russian"},
                },
            },
            "biography": {"type": "text", "analyzer": "russian"},
            "birth_date": {"type": "date"},
            "death_date": {"type": "date"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
        }
    }

    def __init__(self, elasticsearch: AsyncElasticsearch) -> None:
        """Инициализация сервиса"""
        self.es = elasticsearch

    async def setup(self) -> None:
        """Настройка индексов"""
        # Создаем индекс для книг
        if not await self.es.indices.exists(index=self.BOOKS_INDEX):
            await self.es.indices.create(
                index=self.BOOKS_INDEX,
                mappings=self.BOOKS_MAPPING,
                settings={
                    "analysis": {
                        "analyzer": {
                            "russian": {
                                "tokenizer": "standard",
                                "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                            }
                        },
                        "filter": {
                            "russian_stop": {
                                "type": "stop",
                                "stopwords": "_russian_",
                            },
                            "russian_stemmer": {
                                "type": "stemmer",
                                "language": "russian",
                            },
                        },
                    }
                },
            )

        # Создаем индекс для авторов
        if not await self.es.indices.exists(index=self.AUTHORS_INDEX):
            await self.es.indices.create(
                index=self.AUTHORS_INDEX,
                mappings=self.AUTHORS_MAPPING,
                settings={
                    "analysis": {
                        "analyzer": {
                            "russian": {
                                "tokenizer": "standard",
                                "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                            }
                        },
                        "filter": {
                            "russian_stop": {
                                "type": "stop",
                                "stopwords": "_russian_",
                            },
                            "russian_stemmer": {
                                "type": "stemmer",
                                "language": "russian",
                            },
                        },
                    }
                },
            )

    async def index_book(self, book_data: Dict[str, Any]) -> None:
        """Индексация книги"""
        await self.es.index(
            index=self.BOOKS_INDEX,
            id=str(book_data["id"]),
            document=book_data,
        )

    async def index_author(self, author_data: Dict[str, Any]) -> None:
        """Индексация автора"""
        await self.es.index(
            index=self.AUTHORS_INDEX,
            id=str(author_data["id"]),
            document=author_data,
        )

    async def delete_book(self, book_id: UUID) -> None:
        """Удаление книги из индекса"""
        try:
            await self.es.delete(
                index=self.BOOKS_INDEX,
                id=str(book_id),
            )
        except NotFoundError:
            pass

    async def delete_author(self, author_id: UUID) -> None:
        """Удаление автора из индекса"""
        try:
            await self.es.delete(
                index=self.AUTHORS_INDEX,
                id=str(author_id),
            )
        except NotFoundError:
            pass

    async def search_books(
        self,
        params: BookSearchParams,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Поиск книг"""
        # Формируем поисковый запрос
        query: Dict[str, Any] = {"bool": {"must": [], "filter": []}}

        # Поиск по тексту
        if params.query:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": params.query,
                    "fields": ["title^3", "description", "isbn"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            })

        # Фильтры
        if params.language:
            query["bool"]["filter"].append({"term": {"language": params.language}})
        if params.publisher_id:
            query["bool"]["filter"].append({"term": {"publisher_id": str(params.publisher_id)}})
        if params.author_id:
            query["bool"]["filter"].append({"term": {"author_ids": str(params.author_id)}})
        if params.start_date:
            query["bool"]["filter"].append({"range": {"publication_date": {"gte": params.start_date}}})
        if params.end_date:
            query["bool"]["filter"].append({"range": {"publication_date": {"lte": params.end_date}}})

        # Выполняем поиск
        response = await self.es.search(
            index=self.BOOKS_INDEX,
            query=query,
            sort=[{"_score": "desc"}, {"created_at": "desc"}],
            from_=params.skip,
            size=params.limit,
            track_total_hits=True,
        )

        # Возвращаем результаты и общее количество
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        return [hit["_source"] for hit in hits], total

    async def search_authors(
        self,
        params: AuthorSearchParams,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Поиск авторов"""
        # Формируем поисковый запрос
        query: Dict[str, Any] = {"bool": {"must": [], "filter": []}}

        # Поиск по тексту
        if params.query:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": params.query,
                    "fields": ["name^3", "biography"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            })

        # Фильтры по годам
        if params.birth_year:
            query["bool"]["filter"].append({
                "range": {
                    "birth_date": {
                        "gte": f"{params.birth_year}-01-01",
                        "lte": f"{params.birth_year}-12-31",
                    }
                }
            })
        if params.death_year:
            query["bool"]["filter"].append({
                "range": {
                    "death_date": {
                        "gte": f"{params.death_year}-01-01",
                        "lte": f"{params.death_year}-12-31",
                    }
                }
            })

        # Выполняем поиск
        response = await self.es.search(
            index=self.AUTHORS_INDEX,
            query=query,
            sort=[{"_score": "desc"}, {"name.keyword": "asc"}],
            from_=params.skip,
            size=params.limit,
            track_total_hits=True,
        )

        # Возвращаем результаты и общее количество
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        return [hit["_source"] for hit in hits], total

    async def suggest_books(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Подсказки для поиска книг"""
        response = await self.es.search(
            index=self.BOOKS_INDEX,
            suggest={
                "title_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "title.suggest",
                        "size": limit,
                        "skip_duplicates": True,
                    },
                }
            },
            _source=["id", "title"],
        )

        suggestions = response["suggest"]["title_suggest"][0]["options"]
        return [{"id": s["_source"]["id"], "title": s["_source"]["title"]} for s in suggestions]

    async def suggest_authors(self, prefix: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Подсказки для поиска авторов"""
        response = await self.es.search(
            index=self.AUTHORS_INDEX,
            suggest={
                "name_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "name.suggest",
                        "size": limit,
                        "skip_duplicates": True,
                    },
                }
            },
            _source=["id", "name"],
        )

        suggestions = response["suggest"]["name_suggest"][0]["options"]
        return [{"id": s["_source"]["id"], "name": s["_source"]["name"]} for s in suggestions] 