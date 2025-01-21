from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from books_portal.domain.interfaces.auth import AuthService
from books_portal.infrastructure.config.settings import settings


class JWTAuthService(AuthService):
    """Сервис аутентификации на основе JWT токенов"""

    def __init__(self) -> None:
        """Инициализация сервиса"""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return self.pwd_context.verify(plain_password, hashed_password)

    async def create_access_token(self, user_id: UUID) -> str:
        """Создание access token"""
        expires_delta = timedelta(minutes=self.access_token_expire)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
        }
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )

    async def create_refresh_token(self, user_id: UUID) -> str:
        """Создание refresh token"""
        expires_delta = timedelta(days=self.refresh_token_expire)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
        }
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )

    async def verify_token(self, token: str) -> UUID:
        """Проверка токена"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            # Проверяем тип токена
            token_type = payload.get("type")
            if token_type not in ["access", "refresh"]:
                raise JWTError("Invalid token type")
            
            # Получаем ID пользователя
            user_id = payload.get("sub")
            if user_id is None:
                raise JWTError("Token has no user ID")
            
            return UUID(user_id)
            
        except JWTError as e:
            raise JWTError(f"Invalid token: {str(e)}")
        
    async def create_password_reset_token(self, user_id: UUID) -> str:
        """Создание токена для сброса пароля"""
        expire = datetime.utcnow() + timedelta(hours=1)
        
        to_encode = {
            "sub": str(user_id),
            "type": "reset",
            "exp": expire,
        }
        
        return jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )
        
    async def verify_password_reset_token(self, token: str) -> Optional[UUID]:
        """Проверка токена для сброса пароля"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            # Проверяем тип токена
            if payload.get("type") != "reset":
                return None
            
            # Получаем ID пользователя
            user_id = payload.get("sub")
            if user_id is None:
                return None
            
            return UUID(user_id)
            
        except JWTError:
            return None 