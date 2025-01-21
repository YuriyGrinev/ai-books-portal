from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.user import UserRole
from ....infrastructure.database.session import get_async_session
from ....infrastructure.repositories.comment import SQLCommentRepository
from ..dependencies.auth import check_role, get_current_user_with_data
from ..schemas.comments import (
    CommentCreate,
    CommentDetailResponse,
    CommentResponse,
    CommentSearchParams,
    CommentUpdate,
)

router = APIRouter()


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment: CommentCreate,
    current_user_id: Annotated[UUID, Depends(get_current_user_with_data)],
    session: AsyncSession = Depends(get_async_session),
) -> CommentResponse:
    """Создание нового комментария"""
    comment_repo = SQLCommentRepository(session)

    # Если это ответ на комментарий, проверяем, что родительский комментарий существует
    if comment.parent_id:
        parent_comment = await comment_repo.get(comment.parent_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )
        # Проверяем, что родительский комментарий относится к той же книге
        if parent_comment.book_id != comment.book_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment belongs to different book",
            )

    # Создаем комментарий
    return await comment_repo.create(
        content=comment.content,
        book_id=comment.book_id,
        user_id=current_user_id,
        parent_id=comment.parent_id,
    )


@router.get("", response_model=List[CommentResponse])
async def search_comments(
    params: Annotated[CommentSearchParams, Depends()],
    session: AsyncSession = Depends(get_async_session),
) -> List[CommentResponse]:
    """Поиск комментариев"""
    comment_repo = SQLCommentRepository(session)
    return await comment_repo.search(**params.model_dump())


@router.get("/{comment_id}", response_model=CommentDetailResponse)
async def get_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
) -> CommentDetailResponse:
    """Получение информации о комментарии"""
    comment_repo = SQLCommentRepository(session)
    comment = await comment_repo.get_with_replies(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return comment


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    comment: CommentUpdate,
    current_user_id: Annotated[UUID, Depends(get_current_user_with_data)],
    session: AsyncSession = Depends(get_async_session),
) -> CommentResponse:
    """Обновление комментария"""
    comment_repo = SQLCommentRepository(session)

    # Получаем комментарий
    existing_comment = await comment_repo.get(comment_id)
    if not existing_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Проверяем права на редактирование
    if existing_comment.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Обновляем комментарий
    return await comment_repo.update(comment_id, comment.model_dump())


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    current_user_id: Annotated[UUID, Depends(get_current_user_with_data)],
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Удаление комментария"""
    comment_repo = SQLCommentRepository(session)

    # Получаем комментарий
    comment = await comment_repo.get(comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Проверяем права на удаление
    if comment.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Помечаем комментарий как удаленный
    await comment_repo.soft_delete(comment_id) 