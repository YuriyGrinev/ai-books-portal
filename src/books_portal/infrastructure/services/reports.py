from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, func, extract, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from ...domain.interfaces.cache import CacheService
from ...domain.interfaces.reports import ReportService
from ...domain.interfaces.storage import StorageService
from ...infrastructure.database.models import Book, User, Comment, Author, Publisher


class SQLReportService(ReportService):
    def __init__(
        self,
        session: AsyncSession,
        cache_service: CacheService,
        storage_service: StorageService,
    ):
        self.session = session
        self.cache_service = cache_service
        self.storage_service = storage_service

    async def _get_cached_report(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получает отчет из кэша."""
        return await self.cache_service.get(cache_key)

    async def _cache_report(
        self, cache_key: str, report: Dict[str, Any], expire: int = 3600
    ) -> None:
        """Сохраняет отчет в кэш."""
        await self.cache_service.set(cache_key, report, expire=expire)

    async def _get_books_by_month(
        self, query: Select, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Получает статистику по месяцам."""
        month_query = query.with_only_columns(
            func.date_trunc("month", Book.created_at).label("month"),
            func.count().label("count"),
        ).group_by(text("month")).order_by(text("month"))

        result = await self.session.execute(month_query)
        months = []
        for row in result:
            months.append({
                "month": row.month.strftime("%Y-%m"),
                "count": row.count
            })
        return months

    async def generate_books_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Генерирует отчет по книгам."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Пробуем получить из кэша
        cache_key = f"books_report:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_report = await self._get_cached_report(cache_key)
        if cached_report:
            return cached_report

        # Базовый запрос для книг за период
        base_query = select(Book).where(Book.created_at.between(start_date, end_date))

        # Общая статистика
        total_books = await self.session.scalar(select(func.count(Book.id)))
        new_books = await self.session.scalar(
            select(func.count(Book.id))
            .where(Book.created_at.between(start_date, end_date))
        )

        # Статистика по языкам
        languages_query = select(Book.language, func.count(Book.id)) \
            .group_by(Book.language)
        languages_result = await self.session.execute(languages_query)
        languages = {lang: count for lang, count in languages_result}

        # Топ издательств
        top_publishers_query = select(
            Publisher.name,
            func.count(Book.id).label('book_count')
        ).join(Book).group_by(Publisher.name) \
         .order_by(func.count(Book.id).desc()) \
         .limit(10)
        top_publishers_result = await self.session.execute(top_publishers_query)
        top_publishers = {name: count for name, count in top_publishers_result}

        # Динамика по месяцам
        books_by_month = await self._get_books_by_month(base_query, start_date, end_date)

        # Дополнительная статистика
        avg_pages = await self.session.scalar(
            select(func.avg(Book.page_count))
        ) or 0.0

        books_with_files = await self.session.scalar(
            select(func.count(Book.id)).where(Book.file_url.isnot(None))
        )

        books_with_covers = await self.session.scalar(
            select(func.count(Book.id)).where(Book.cover_url.isnot(None))
        )

        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_books": total_books,
            "new_books": new_books,
            "languages": languages,
            "top_publishers": top_publishers,
            "books_by_month": books_by_month,
            "avg_pages": round(avg_pages, 2),
            "books_with_files": books_with_files,
            "books_with_covers": books_with_covers
        }

        # Кэшируем результат
        await self._cache_report(cache_key, report)

        return report

    async def generate_users_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Генерирует отчет по пользователям."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Пробуем получить из кэша
        cache_key = f"users_report:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_report = await self._get_cached_report(cache_key)
        if cached_report:
            return cached_report

        # Общая статистика
        total_users = await self.session.scalar(select(func.count(User.id)))
        new_users = await self.session.scalar(
            select(func.count(User.id))
            .where(User.created_at.between(start_date, end_date))
        )
        blocked_users = await self.session.scalar(
            select(func.count(User.id)).where(User.is_blocked == True)
        )

        # Статистика по ролям
        roles_query = select(User.role, func.count(User.id)) \
            .group_by(User.role)
        roles_result = await self.session.execute(roles_query)
        roles = {role: count for role, count in roles_result}

        # Активные пользователи
        active_users_query = select(
            User.username,
            func.count(Comment.id).label('comment_count'),
            func.count(func.distinct(Comment.book_id)).label('books_commented')
        ).join(Comment).group_by(User.username) \
         .order_by(func.count(Comment.id).desc()) \
         .limit(10)
        active_users_result = await self.session.execute(active_users_query)
        active_users = []
        for row in active_users_result:
            active_users.append({
                "username": row.username,
                "comments_count": row.comment_count,
                "books_commented": row.books_commented
            })

        # Динамика регистраций по месяцам
        users_by_month = await self._get_books_by_month(
            select(User).where(User.created_at.between(start_date, end_date)),
            start_date,
            end_date
        )

        # Дополнительная статистика
        avg_comments = await self.session.scalar(
            select(func.avg(
                select(func.count(Comment.id))
                .where(Comment.user_id == User.id)
                .scalar_subquery()
            ))
        ) or 0.0

        users_with_avatar = await self.session.scalar(
            select(func.count(User.id)).where(User.avatar_url.isnot(None))
        )

        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_users": total_users,
            "new_users": new_users,
            "blocked_users": blocked_users,
            "roles": roles,
            "active_users": active_users,
            "users_by_month": users_by_month,
            "avg_comments_per_user": round(avg_comments, 2),
            "users_with_avatar": users_with_avatar
        }

        # Кэшируем результат
        await self._cache_report(cache_key, report)

        return report

    async def generate_comments_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Генерирует отчет по комментариям."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        # Пробуем получить из кэша
        cache_key = f"comments_report:{start_date.isoformat()}:{end_date.isoformat()}"
        cached_report = await self._get_cached_report(cache_key)
        if cached_report:
            return cached_report

        # Общая статистика
        total_comments = await self.session.scalar(select(func.count(Comment.id)))
        new_comments = await self.session.scalar(
            select(func.count(Comment.id))
            .where(Comment.created_at.between(start_date, end_date))
        )
        deleted_comments = await self.session.scalar(
            select(func.count(Comment.id)).where(Comment.is_deleted == True)
        )

        # Топ книг по комментариям
        top_books_query = select(
            Book.title,
            func.count(Comment.id).label('total_comments'),
            func.count(case((Comment.is_deleted == True, 1))).label('deleted_comments')
        ).join(Comment).group_by(Book.title) \
         .order_by(func.count(Comment.id).desc()) \
         .limit(10)
        top_books_result = await self.session.execute(top_books_query)
        top_books = []
        for row in top_books_result:
            top_books.append({
                "book_title": row.title,
                "total_comments": row.total_comments,
                "deleted_comments": row.deleted_comments
            })

        # Динамика комментариев по месяцам
        comments_by_month = await self._get_books_by_month(
            select(Comment).where(Comment.created_at.between(start_date, end_date)),
            start_date,
            end_date
        )

        # Дополнительная статистика
        avg_comments_per_book = await self.session.scalar(
            select(func.avg(
                select(func.count(Comment.id))
                .where(Comment.book_id == Book.id)
                .scalar_subquery()
            ))
        ) or 0.0

        replies_count = await self.session.scalar(
            select(func.count(Comment.id)).where(Comment.parent_id.isnot(None))
        )

        avg_depth_query = select(func.avg(
            select(func.count(Comment.id))
            .where(Comment.parent_id == Comment.id)
            .scalar_subquery()
        ))
        avg_comment_depth = await self.session.scalar(avg_depth_query) or 1.0

        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_comments": total_comments,
            "new_comments": new_comments,
            "deleted_comments": deleted_comments,
            "top_books": top_books,
            "comments_by_month": comments_by_month,
            "avg_comments_per_book": round(avg_comments_per_book, 2),
            "replies_count": replies_count,
            "avg_comment_depth": round(avg_comment_depth, 2)
        }

        # Кэшируем результат
        await self._cache_report(cache_key, report)

        return report

    async def generate_storage_report(self) -> Dict[str, Any]:
        """Генерирует отчет по использованию хранилища."""
        # Пробуем получить из кэша
        cache_key = "storage_report"
        cached_report = await self._get_cached_report(cache_key)
        if cached_report:
            return cached_report

        # Статистика по книгам
        books_stats = await self._get_storage_stats("books")
        covers_stats = await self._get_storage_stats("covers")
        author_photos_stats = await self._get_storage_stats("author_photos")
        publisher_logos_stats = await self._get_storage_stats("publisher_logos")

        total_size = (
            books_stats["total_size"] +
            covers_stats["total_size"] +
            author_photos_stats["total_size"] +
            publisher_logos_stats["total_size"]
        )

        total_files = (
            books_stats["count"] +
            covers_stats["count"] +
            author_photos_stats["count"] +
            publisher_logos_stats["count"]
        )

        report = {
            "books": books_stats,
            "covers": covers_stats,
            "author_photos": author_photos_stats,
            "publisher_logos": publisher_logos_stats,
            "total_size": total_size,
            "total_files": total_files
        }

        # Кэшируем результат на более длительный срок
        await self._cache_report(cache_key, report, expire=7200)

        return report

    async def _get_storage_stats(self, file_type: str) -> Dict[str, Any]:
        """Получает статистику по определенному типу файлов."""
        # Здесь должна быть логика получения статистики из хранилища
        # Для примера возвращаем заглушку
        return {
            "total_size": 0,
            "count": 0,
            "avg_size": 0.0
        } 