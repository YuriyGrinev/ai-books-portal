import json
from typing import Any, Optional

from redis.asyncio import Redis

from ....domain.ports.services.cache import CacheService
from ...config.settings import settings


class RedisCacheService(CacheService):
    """Redis cache service implementation"""

    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        self._ensure_connection()

    async def _ensure_connection(self) -> None:
        """Ensure Redis connection is alive"""
        await self.redis.ping()

    def _serialize(self, value: Any) -> str:
        """Serialize value to string"""
        return json.dumps(value)

    def _deserialize(self, value: str) -> Any:
        """Deserialize value from string"""
        return json.loads(value)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception:
            return None

    async def set(self, key: str, value: Any, expire: int = 0) -> bool:
        """Set value in cache with optional expiration time in seconds"""
        try:
            serialized_value = self._serialize(value)
            if expire > 0:
                await self.redis.setex(key, expire, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception:
            return False

    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            await self.redis.flushdb()
            return True
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(await self.redis.exists(key))
        except Exception:
            return False 