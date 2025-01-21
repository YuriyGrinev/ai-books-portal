from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from ....domain.entities.user import User, UserRole
from ....domain.ports.services.auth import AuthService
from ...config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTAuthService(AuthService):
    """JWT authentication service implementation"""

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    async def create_access_token(self, user_id: UUID) -> str:
        """Create access token for user"""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def create_refresh_token(self, user_id: UUID) -> str:
        """Create refresh token for user"""
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    async def verify_token(self, token: str) -> Optional[UUID]:
        """Verify token and return user ID if valid"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return UUID(user_id)
        except (JWTError, ValueError):
            return None

    def hash_password(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)

    async def check_permission(self, user: User, required_role: UserRole) -> bool:
        """Check if user has required role"""
        # Роли по уровню доступа (от высшего к низшему)
        role_hierarchy = {
            UserRole.ADMIN: 5,
            UserRole.EDITOR: 4,
            UserRole.MODERATOR: 3,
            UserRole.USER: 2,
            UserRole.GUEST: 1
        }

        if not user.is_active or user.is_blocked:
            return False

        return role_hierarchy[user.role] >= role_hierarchy[required_role] 