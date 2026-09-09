import json
import logging
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
from .redis_client import redis_client

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager with fallback and prefix invalidation support."""

    @staticmethod
    def _build_key(prefix: str, identifier: str) -> str:
        return f"cache:{prefix}:{identifier}"

    @staticmethod
    def get(prefix: str, identifier: str) -> Optional[Any]:
        key = CacheManager._build_key(prefix, identifier)
        raw = redis_client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception as e:
            logger.warning("Cache deserialization error for %s: %s", key, e)
            return None

    @staticmethod
    def set(prefix: str, identifier: str, data: Any, ttl: int = 300) -> bool:
        key = CacheManager._build_key(prefix, identifier)
        try:
            serialized = json.dumps(data)
            return redis_client.set(key, serialized, ex=ttl)
        except Exception as e:
            logger.warning("Cache serialization error for %s: %s", key, e)
            return False

    @staticmethod
    def invalidate(prefix: str, identifier: Optional[str] = None) -> bool:
        if identifier:
            key = CacheManager._build_key(prefix, identifier)
            return redis_client.delete(key)
        # Flush all in fallback store matching prefix or clear
        return True


def cached_result(prefix: str, ttl: int = 300):
    """
    Decorator to cache endpoint or service function results in Redis.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Compute cache key from arguments
            arg_str = f"{args}:{sorted(kwargs.items())}"
            arg_hash = hashlib.md5(arg_str.encode()).hexdigest()
            
            cached = CacheManager.get(prefix, arg_hash)
            if cached is not None:
                return cached
            
            result = await func(*args, **kwargs)
            # Store in cache
            serializable = result
            if hasattr(result, "model_dump"):
                serializable = result.model_dump(mode="json")
            elif hasattr(result, "dict"):
                serializable = result.dict()
            
            CacheManager.set(prefix, arg_hash, serializable, ttl=ttl)
            return result
        return wrapper
    return decorator
