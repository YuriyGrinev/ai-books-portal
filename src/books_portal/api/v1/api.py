from fastapi import APIRouter

from .endpoints import auth, books, authors, publishers, users, comments

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

api_router.include_router(
    books.router,
    prefix="/books",
    tags=["books"]
)

api_router.include_router(
    authors.router,
    prefix="/authors",
    tags=["authors"]
)

api_router.include_router(
    publishers.router,
    prefix="/publishers",
    tags=["publishers"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    comments.router,
    prefix="/comments",
    tags=["comments"]
) 