from typing import Dict, Optional

from prometheus_client import Counter, Gauge, Histogram

from books_portal.domain.interfaces.metrics import MetricsService


class PrometheusMetricsService(MetricsService):
    """Сервис сбора метрик на основе Prometheus"""

    def __init__(self) -> None:
        """Инициализация сервиса"""
        # Метрики для HTTP запросов
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total number of HTTP requests",
            ["method", "endpoint", "status"],
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
        )
        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests in progress",
            ["method", "endpoint"],
        )

        # Метрики для базы данных
        self.db_queries_total = Counter(
            "db_queries_total",
            "Total number of database queries",
            ["operation", "table"],
        )
        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation", "table"],
        )
        self.db_connections_in_use = Gauge(
            "db_connections_in_use",
            "Number of database connections currently in use",
        )
        self.db_connection_pool_size = Gauge(
            "db_connection_pool_size",
            "Size of the database connection pool",
        )

        # Метрики для кэша
        self.cache_hits_total = Counter(
            "cache_hits_total",
            "Total number of cache hits",
            ["operation"],
        )
        self.cache_misses_total = Counter(
            "cache_misses_total",
            "Total number of cache misses",
            ["operation"],
        )
        self.cache_operations_total = Counter(
            "cache_operations_total",
            "Total number of cache operations",
            ["operation"],
        )

        # Метрики для поиска
        self.search_requests_total = Counter(
            "search_requests_total",
            "Total number of search requests",
            ["index", "operation"],
        )
        self.search_request_duration_seconds = Histogram(
            "search_request_duration_seconds",
            "Search request duration in seconds",
            ["index", "operation"],
        )

        # Метрики для файлового хранилища
        self.storage_operations_total = Counter(
            "storage_operations_total",
            "Total number of storage operations",
            ["operation"],
        )
        self.storage_operation_duration_seconds = Histogram(
            "storage_operation_duration_seconds",
            "Storage operation duration in seconds",
            ["operation"],
        )
        self.storage_bytes_total = Counter(
            "storage_bytes_total",
            "Total number of bytes stored",
            ["operation"],
        )

        # Метрики для уведомлений
        self.notifications_sent_total = Counter(
            "notifications_sent_total",
            "Total number of notifications sent",
            ["type"],
        )
        self.notification_errors_total = Counter(
            "notification_errors_total",
            "Total number of notification errors",
            ["type"],
        )

        # Бизнес-метрики
        self.users_total = Gauge(
            "users_total",
            "Total number of users",
            ["role", "status"],
        )
        self.books_total = Gauge(
            "books_total",
            "Total number of books",
            ["language"],
        )
        self.authors_total = Gauge(
            "authors_total",
            "Total number of authors",
        )
        self.comments_total = Gauge(
            "comments_total",
            "Total number of comments",
            ["status"],
        )

    async def observe_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ) -> None:
        """Регистрация HTTP запроса"""
        labels = {"method": method, "endpoint": endpoint}
        status_labels = {**labels, "status": str(status)}

        self.http_requests_total.labels(**status_labels).inc()
        self.http_request_duration_seconds.labels(**labels).observe(duration)

    async def start_http_request(
        self,
        method: str,
        endpoint: str,
    ) -> None:
        """Начало HTTP запроса"""
        self.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint,
        ).inc()

    async def end_http_request(
        self,
        method: str,
        endpoint: str,
    ) -> None:
        """Окончание HTTP запроса"""
        self.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint,
        ).dec()

    async def observe_db_query(
        self,
        operation: str,
        table: str,
        duration: float,
    ) -> None:
        """Регистрация запроса к базе данных"""
        labels = {"operation": operation, "table": table}
        
        self.db_queries_total.labels(**labels).inc()
        self.db_query_duration_seconds.labels(**labels).observe(duration)

    async def set_db_connections(
        self,
        in_use: int,
        pool_size: int,
    ) -> None:
        """Установка количества соединений с базой данных"""
        self.db_connections_in_use.set(in_use)
        self.db_connection_pool_size.set(pool_size)

    async def observe_cache_operation(
        self,
        operation: str,
        hit: Optional[bool] = None,
    ) -> None:
        """Регистрация операции с кэшем"""
        self.cache_operations_total.labels(operation=operation).inc()
        
        if hit is not None:
            if hit:
                self.cache_hits_total.labels(operation=operation).inc()
            else:
                self.cache_misses_total.labels(operation=operation).inc()

    async def observe_search_request(
        self,
        index: str,
        operation: str,
        duration: float,
    ) -> None:
        """Регистрация поискового запроса"""
        labels = {"index": index, "operation": operation}
        
        self.search_requests_total.labels(**labels).inc()
        self.search_request_duration_seconds.labels(**labels).observe(duration)

    async def observe_storage_operation(
        self,
        operation: str,
        duration: float,
        bytes_count: Optional[int] = None,
    ) -> None:
        """Регистрация операции с файловым хранилищем"""
        self.storage_operations_total.labels(operation=operation).inc()
        self.storage_operation_duration_seconds.labels(operation=operation).observe(duration)
        
        if bytes_count is not None:
            self.storage_bytes_total.labels(operation=operation).inc(bytes_count)

    async def observe_notification(
        self,
        notification_type: str,
        success: bool,
    ) -> None:
        """Регистрация отправки уведомления"""
        if success:
            self.notifications_sent_total.labels(type=notification_type).inc()
        else:
            self.notification_errors_total.labels(type=notification_type).inc()

    async def set_users_count(
        self,
        counts: Dict[str, Dict[str, int]],
    ) -> None:
        """Установка количества пользователей"""
        for role, statuses in counts.items():
            for status, count in statuses.items():
                self.users_total.labels(role=role, status=status).set(count)

    async def set_books_count(
        self,
        counts: Dict[str, int],
    ) -> None:
        """Установка количества книг"""
        for language, count in counts.items():
            self.books_total.labels(language=language).set(count)

    async def set_authors_count(
        self,
        count: int,
    ) -> None:
        """Установка количества авторов"""
        self.authors_total.set(count)

    async def set_comments_count(
        self,
        counts: Dict[str, int],
    ) -> None:
        """Установка количества комментариев"""
        for status, count in counts.items():
            self.comments_total.labels(status=status).set(count) 