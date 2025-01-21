import json
from typing import Any, Optional

import redis.asyncio as redis

from books_portal.domain.interfaces.cache import CacheService


class RedisCacheService(CacheService):
    """Сервис кэширования на основе Redis"""

    def __init__(self, redis_client: redis.Redis) -> None:
        """Инициализация сервиса"""
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode cached value: {str(e)}")

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
    ) -> None:
        """Установка значения в кэш"""
        try:
            json_value = json.dumps(value)
            if expire is not None:
                await self.redis.setex(key, expire, json_value)
            else:
                await self.redis.set(key, json_value)
        except TypeError as e:
            raise TypeError(f"Failed to encode value: {str(e)}")

    async def delete(self, key: str) -> None:
        """Удаление значения из кэша"""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        return await self.redis.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> None:
        """Установка времени жизни для ключа"""
        await self.redis.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Получение оставшегося времени жизни ключа"""
        return await self.redis.ttl(key)

    async def incr(self, key: str) -> int:
        """Инкремент значения"""
        return await self.redis.incr(key)

    async def decr(self, key: str) -> int:
        """Декремент значения"""
        return await self.redis.decr(key)

    async def sadd(self, key: str, *values: Any) -> int:
        """Добавление значений в множество"""
        json_values = [json.dumps(value) for value in values]
        return await self.redis.sadd(key, *json_values)

    async def srem(self, key: str, *values: Any) -> int:
        """Удаление значений из множества"""
        json_values = [json.dumps(value) for value in values]
        return await self.redis.srem(key, *json_values)

    async def smembers(self, key: str) -> set[Any]:
        """Получение всех значений множества"""
        values = await self.redis.smembers(key)
        return {json.loads(value) for value in values}

    async def sismember(self, key: str, value: Any) -> bool:
        """Проверка наличия значения в множестве"""
        json_value = json.dumps(value)
        return await self.redis.sismember(key, json_value)

    async def lpush(self, key: str, *values: Any) -> int:
        """Добавление значений в начало списка"""
        json_values = [json.dumps(value) for value in values]
        return await self.redis.lpush(key, *json_values)

    async def rpush(self, key: str, *values: Any) -> int:
        """Добавление значений в конец списка"""
        json_values = [json.dumps(value) for value in values]
        return await self.redis.rpush(key, *json_values)

    async def lpop(self, key: str) -> Optional[Any]:
        """Получение и удаление первого элемента списка"""
        value = await self.redis.lpop(key)
        if value is None:
            return None
        return json.loads(value)

    async def rpop(self, key: str) -> Optional[Any]:
        """Получение и удаление последнего элемента списка"""
        value = await self.redis.rpop(key)
        if value is None:
            return None
        return json.loads(value)

    async def lrange(self, key: str, start: int, end: int) -> list[Any]:
        """Получение диапазона значений из списка"""
        values = await self.redis.lrange(key, start, end)
        return [json.loads(value) for value in values]

    async def llen(self, key: str) -> int:
        """Получение длины списка"""
        return await self.redis.llen(key)

    async def flushall(self) -> None:
        """Очистка всего кэша"""
        await self.redis.flushall() 