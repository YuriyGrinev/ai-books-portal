from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field


class PeriodInfo(BaseModel):
    start: datetime
    end: datetime


class BooksByMonth(BaseModel):
    month: str = Field(description="Месяц в формате YYYY-MM")
    count: int = Field(description="Количество книг")


class BooksReport(BaseModel):
    period: PeriodInfo
    total_books: int = Field(description="Общее количество книг")
    new_books: int = Field(description="Количество новых книг за период")
    languages: Dict[str, int] = Field(description="Статистика по языкам")
    top_publishers: Dict[str, int] = Field(description="Топ издательств по количеству книг")
    books_by_month: List[BooksByMonth] = Field(description="Динамика добавления книг по месяцам")
    avg_pages: float = Field(description="Среднее количество страниц")
    books_with_files: int = Field(description="Количество книг с файлами")
    books_with_covers: int = Field(description="Количество книг с обложками")


class UserActivity(BaseModel):
    username: str = Field(description="Имя пользователя")
    comments_count: int = Field(description="Количество комментариев")
    books_commented: int = Field(description="Количество прокомментированных книг")


class UsersReport(BaseModel):
    period: PeriodInfo
    total_users: int = Field(description="Общее количество пользователей")
    new_users: int = Field(description="Количество новых пользователей за период")
    blocked_users: int = Field(description="Количество заблокированных пользователей")
    roles: Dict[str, int] = Field(description="Статистика по ролям")
    active_users: List[UserActivity] = Field(description="Топ активных пользователей")
    users_by_month: List[BooksByMonth] = Field(description="Динамика регистраций по месяцам")
    avg_comments_per_user: float = Field(description="Среднее количество комментариев на пользователя")
    users_with_avatar: int = Field(description="Количество пользователей с аватарами")


class CommentsByBook(BaseModel):
    book_title: str = Field(description="Название книги")
    total_comments: int = Field(description="Общее количество комментариев")
    deleted_comments: int = Field(description="Количество удаленных комментариев")


class CommentsReport(BaseModel):
    period: PeriodInfo
    total_comments: int = Field(description="Общее количество комментариев")
    new_comments: int = Field(description="Количество новых комментариев за период")
    deleted_comments: int = Field(description="Количество удаленных комментариев")
    top_books: List[CommentsByBook] = Field(description="Топ книг по комментариям")
    comments_by_month: List[BooksByMonth] = Field(description="Динамика комментариев по месяцам")
    avg_comments_per_book: float = Field(description="Среднее количество комментариев на книгу")
    replies_count: int = Field(description="Количество ответов на комментарии")
    avg_comment_depth: float = Field(description="Средняя глубина обсуждений")


class StorageStats(BaseModel):
    total_size: int = Field(description="Общий размер в байтах")
    count: int = Field(description="Количество файлов")
    avg_size: float = Field(description="Средний размер файла в байтах")


class StorageReport(BaseModel):
    books: StorageStats = Field(description="Статистика по файлам книг")
    covers: StorageStats = Field(description="Статистика по обложкам")
    author_photos: StorageStats = Field(description="Статистика по фото авторов")
    publisher_logos: StorageStats = Field(description="Статистика по логотипам издательств")
    total_size: int = Field(description="Общий размер всех файлов в байтах")
    total_files: int = Field(description="Общее количество файлов")


class ReportParams(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Начало периода")
    end_date: Optional[datetime] = Field(None, description="Конец периода") 