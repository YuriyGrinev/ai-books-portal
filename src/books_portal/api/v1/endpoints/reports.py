from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.interfaces.cache import CacheService
from ....domain.interfaces.reports import ReportService
from ....domain.interfaces.storage import StorageService
from ....infrastructure.database.session import get_async_session
from ....infrastructure.services.cache import RedisCacheService
from ....infrastructure.services.reports import SQLReportService
from ....infrastructure.services.storage import MinioStorageService
from ..dependencies import require_admin
from ..schemas.reports import (
    BooksReport,
    UsersReport,
    CommentsReport,
    StorageReport,
    ReportParams,
)

router = APIRouter(prefix="/reports", tags=["reports"])


async def get_report_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    cache_service: Annotated[CacheService, Depends(RedisCacheService)],
    storage_service: Annotated[StorageService, Depends(MinioStorageService)],
) -> ReportService:
    return SQLReportService(session, cache_service, storage_service)


@router.get(
    "/books",
    response_model=BooksReport,
    dependencies=[Depends(require_admin)],
    summary="Получить отчет по книгам",
    description="Возвращает статистику по книгам за указанный период",
)
async def get_books_report(
    params: Annotated[ReportParams, Depends()],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    force_refresh: bool = Query(
        False,
        description="Принудительно обновить отчет, игнорируя кэш"
    ),
) -> BooksReport:
    try:
        return await report_service.generate_books_report(
            start_date=params.start_date,
            end_date=params.end_date,
            force_refresh=force_refresh,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации отчета: {str(e)}",
        )


@router.get(
    "/users",
    response_model=UsersReport,
    dependencies=[Depends(require_admin)],
    summary="Получить отчет по пользователям",
    description="Возвращает статистику по пользователям за указанный период",
)
async def get_users_report(
    params: Annotated[ReportParams, Depends()],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    force_refresh: bool = Query(
        False,
        description="Принудительно обновить отчет, игнорируя кэш"
    ),
) -> UsersReport:
    try:
        return await report_service.generate_users_report(
            start_date=params.start_date,
            end_date=params.end_date,
            force_refresh=force_refresh,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации отчета: {str(e)}",
        )


@router.get(
    "/comments",
    response_model=CommentsReport,
    dependencies=[Depends(require_admin)],
    summary="Получить отчет по комментариям",
    description="Возвращает статистику по комментариям за указанный период",
)
async def get_comments_report(
    params: Annotated[ReportParams, Depends()],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    force_refresh: bool = Query(
        False,
        description="Принудительно обновить отчет, игнорируя кэш"
    ),
) -> CommentsReport:
    try:
        return await report_service.generate_comments_report(
            start_date=params.start_date,
            end_date=params.end_date,
            force_refresh=force_refresh,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации отчета: {str(e)}",
        )


@router.get(
    "/storage",
    response_model=StorageReport,
    dependencies=[Depends(require_admin)],
    summary="Получить отчет по хранилищу",
    description="Возвращает статистику по использованию хранилища",
)
async def get_storage_report(
    report_service: Annotated[ReportService, Depends(get_report_service)],
    force_refresh: bool = Query(
        False,
        description="Принудительно обновить отчет, игнорируя кэш"
    ),
) -> StorageReport:
    try:
        return await report_service.generate_storage_report(force_refresh=force_refresh)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации отчета: {str(e)}",
        ) 