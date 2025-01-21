from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from jose import jwt
from passlib.context import CryptContext

from books_portal.infrastructure.config.settings import settings
from books_portal.infrastructure.services.auth import JWTAuthService


@pytest.fixture
def auth_service() -> JWTAuthService:
    """Фикстура для создания сервиса аутентификации"""
    return JWTAuthService()


@pytest.fixture
def test_user_id() -> UUID:
    """Фикстура с тестовым ID пользователя"""
    return uuid4()


@pytest.fixture
def test_password() -> str:
    """Фикстура с тестовым паролем"""
    return "test_password"


def test_hash_password(auth_service: JWTAuthService, test_password: str) -> None:
    """Тест хеширования пароля"""
    # Хешируем пароль
    hashed_password = auth_service.hash_password(test_password)
    
    # Проверяем, что хеш отличается от исходного пароля
    assert hashed_password != test_password
    
    # Проверяем, что пароль верифицируется
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    assert pwd_context.verify(test_password, hashed_password)


def test_verify_password(auth_service: JWTAuthService, test_password: str) -> None:
    """Тест верификации пароля"""
    # Хешируем пароль
    hashed_password = auth_service.hash_password(test_password)
    
    # Проверяем корректный пароль
    assert auth_service.verify_password(test_password, hashed_password)
    
    # Проверяем некорректный пароль
    assert not auth_service.verify_password("wrong_password", hashed_password)


async def test_create_access_token(
    auth_service: JWTAuthService,
    test_user_id: UUID,
) -> None:
    """Тест создания access token"""
    # Создаем токен
    token = await auth_service.create_access_token(test_user_id)
    
    # Декодируем токен
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    
    # Проверяем данные в токене
    assert UUID(payload["sub"]) == test_user_id
    assert payload["type"] == "access"
    
    # Проверяем время жизни токена
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    expected_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    assert abs((exp - expected_exp).total_seconds()) < 1


async def test_create_refresh_token(
    auth_service: JWTAuthService,
    test_user_id: UUID,
) -> None:
    """Тест создания refresh token"""
    # Создаем токен
    token = await auth_service.create_refresh_token(test_user_id)
    
    # Декодируем токен
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    
    # Проверяем данные в токене
    assert UUID(payload["sub"]) == test_user_id
    assert payload["type"] == "refresh"
    
    # Проверяем время жизни токена
    exp = datetime.fromtimestamp(payload["exp"])
    now = datetime.utcnow()
    expected_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    assert abs((exp - expected_exp).total_seconds()) < 1


async def test_verify_token(
    auth_service: JWTAuthService,
    test_user_id: UUID,
) -> None:
    """Тест верификации токена"""
    # Создаем токен
    token = await auth_service.create_access_token(test_user_id)
    
    # Верифицируем токен
    user_id = await auth_service.verify_token(token)
    assert user_id == test_user_id


async def test_verify_expired_token(
    auth_service: JWTAuthService,
    test_user_id: UUID,
) -> None:
    """Тест верификации истекшего токена"""
    # Создаем токен с истекшим временем жизни
    exp = datetime.utcnow() - timedelta(days=1)
    payload = {
        "sub": str(test_user_id),
        "type": "access",
        "exp": exp.timestamp(),
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    # Верифицируем токен
    with pytest.raises(jwt.ExpiredSignatureError):
        await auth_service.verify_token(token)


async def test_verify_invalid_token(auth_service: JWTAuthService) -> None:
    """Тест верификации некорректного токена"""
    # Пробуем верифицировать некорректный токен
    with pytest.raises(jwt.JWTError):
        await auth_service.verify_token("invalid_token")


async def test_verify_token_with_wrong_type(
    auth_service: JWTAuthService,
    test_user_id: UUID,
) -> None:
    """Тест верификации токена с неправильным типом"""
    # Создаем токен с неправильным типом
    payload = {
        "sub": str(test_user_id),
        "type": "wrong_type",
        "exp": (datetime.utcnow() + timedelta(minutes=15)).timestamp(),
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    # Верифицируем токен
    with pytest.raises(jwt.JWTError):
        await auth_service.verify_token(token) 