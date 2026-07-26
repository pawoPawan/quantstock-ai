import json
import logging
from typing import Any, Optional
from functools import wraps

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache GET failed for {key}: {e}")
    return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    try:
        client = await get_redis()
        await client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache SET failed for {key}: {e}")
    return False


async def cache_delete(key: str) -> None:
    try:
        client = await get_redis()
        await client.delete(key)
    except Exception as e:
        logger.warning(f"Cache DELETE failed for {key}: {e}")


async def cache_flush_pattern(pattern: str) -> None:
    try:
        client = await get_redis()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache FLUSH failed for pattern {pattern}: {e}")


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator to cache async function results in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
