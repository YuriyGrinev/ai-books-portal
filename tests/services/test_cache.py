import json
from typing import Any, Dict

import pytest
import redis.asyncio as redis
from pydantic import BaseModel

from books_portal.infrastructure.config.settings import settings
from books_portal.infrastructure.services.cache import RedisCacheService


class TestModel(BaseModel):
    """Тестовая модель для проверки сериализации"""
    id: int
    name: str
    data: Dict[str, Any]


@pytest.fixture
async def redis_client() -> redis.Redis:
    """Фикстура для создания клиента Redis"""
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    yield client
    await client.flushdb()
    await client.close()


@pytest.fixture
def cache_service(redis_client: redis.Redis) -> RedisCacheService:
    """Фикстура для создания сервиса кэширования"""
    return RedisCacheService(redis_client)


@pytest.fixture
def test_data() -> dict:
    """Фикстура с тестовыми данными"""
    return {
        "id": 1,
        "name": "test",
        "data": {"key": "value"},
    }


@pytest.fixture
def test_model(test_data: dict) -> TestModel:
    """Фикстура с тестовой моделью"""
    return TestModel(**test_data)


async def test_set_get_string(cache_service: RedisCacheService) -> None:
    """Тест установки и получения строкового значения"""
    key = "test_string"
    value = "test_value"
    
    # Устанавливаем значение
    await cache_service.set(key, value)
    
    # Получаем значение
    result = await cache_service.get(key)
    assert result == value


async def test_set_get_dict(cache_service: RedisCacheService, test_data: dict) -> None:
    """Тест установки и получения словаря"""
    key = "test_dict"
    
    # Устанавливаем значение
    await cache_service.set(key, test_data)
    
    # Получаем значение
    result = await cache_service.get(key)
    assert result == test_data


async def test_set_get_model(
    cache_service: RedisCacheService,
    test_model: TestModel,
) -> None:
    """Тест установки и получения модели Pydantic"""
    key = "test_model"
    
    # Устанавливаем значение
    await cache_service.set(key, test_model.model_dump())
    
    # Получаем значение
    result = await cache_service.get(key)
    assert result == test_model.model_dump()


async def test_set_with_expire(cache_service: RedisCacheService) -> None:
    """Тест установки значения с временем жизни"""
    key = "test_expire"
    value = "test_value"
    expire = 1  # 1 секунда
    
    # Устанавливаем значение с временем жизни
    await cache_service.set(key, value, expire=expire)
    
    # Проверяем, что значение существует
    result = await cache_service.get(key)
    assert result == value
    
    # Ждем, пока значение истечет
    import asyncio
    await asyncio.sleep(expire + 1)
    
    # Проверяем, что значение удалено
    result = await cache_service.get(key)
    assert result is None


async def test_get_nonexistent_key(cache_service: RedisCacheService) -> None:
    """Тест получения несуществующего ключа"""
    key = "nonexistent"
    result = await cache_service.get(key)
    assert result is None


async def test_delete_key(cache_service: RedisCacheService) -> None:
    """Тест удаления ключа"""
    key = "test_delete"
    value = "test_value"
    
    # Устанавливаем значение
    await cache_service.set(key, value)
    
    # Удаляем ключ
    await cache_service.delete(key)
    
    # Проверяем, что значение удалено
    result = await cache_service.get(key)
    assert result is None


async def test_delete_nonexistent_key(cache_service: RedisCacheService) -> None:
    """Тест удаления несуществующего ключа"""
    key = "nonexistent"
    # Не должно вызывать исключение
    await cache_service.delete(key)


async def test_set_invalid_json(cache_service: RedisCacheService) -> None:
    """Тест установки значения, которое нельзя сериализовать в JSON"""
    key = "test_invalid"
    value = object()  # Объект, который нельзя сериализовать
    
    with pytest.raises(TypeError):
        await cache_service.set(key, value)


async def test_get_invalid_json(
    cache_service: RedisCacheService,
    redis_client: redis.Redis,
) -> None:
    """Тест получения значения с некорректным JSON"""
    key = "test_invalid"
    invalid_json = "{"  # Некорректный JSON
    
    # Напрямую устанавливаем некорректное значение в Redis
    await redis_client.set(key, invalid_json)
    
    with pytest.raises(json.JSONDecodeError):
        await cache_service.get(key) 