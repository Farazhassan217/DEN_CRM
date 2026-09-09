import time
import json
import logging
from typing import Optional, Any
from .config import settings

logger = logging.getLogger(__name__)


class InMemoryFallbackStore:
    """In-memory key-value store with TTL fallback for local dev & testing."""
    def __init__(self):
        self._store: dict[str, tuple[Any, Optional[float]]] = {}

    def get(self, key: str) -> Optional[str]:
        self._purge_expired()
        item = self._store.get(key)
        if item is None:
            return None
        value, expiry = item
        if expiry is not None and time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expiry = time.time() + ex if ex else None
        self._store[key] = (str(value), expiry)
        return True

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def flushdb(self) -> bool:
        self._store.clear()
        return True

    def _purge_expired(self):
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._store.items() if exp is not None and now > exp]
        for k in expired_keys:
            self._store.pop(k, None)


class ResilientRedisClient:
    """
    Resilient Redis client wrapper.
    Attempts live Redis connection, but falls back seamlessly to in-memory store
    if Redis is unavailable or disconnected.
    """
    def __init__(self):
        self._client = None
        self._fallback = InMemoryFallbackStore()
        self._use_fallback = False
        self._init_client()

    def _init_client(self):
        try:
            import redis
            redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
            client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1.0)
            client.ping()
            self._client = client
            self._use_fallback = False
            logger.info("Connected successfully to Redis server at %s", redis_url)
        except Exception as exc:
            logger.info("Redis server not reachable (%s); activating in-memory fallback store", exc)
            self._client = None
            self._use_fallback = True

    @property
    def is_connected(self) -> bool:
        if self._use_fallback or self._client is None:
            return False
        try:
            return bool(self._client.ping())
        except Exception:
            return False

    def ping(self) -> bool:
        """Returns True if live Redis or resilient in-memory fallback is active."""
        if not self._use_fallback and self._client:
            try:
                return bool(self._client.ping())
            except Exception:
                pass
        return True

    def get(self, key: str) -> Optional[str]:
        if not self._use_fallback and self._client:
            try:
                return self._client.get(key)
            except Exception as e:
                logger.warning("Redis get error for %s: %s; falling back to memory store", key, e)
        return self._fallback.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if not self._use_fallback and self._client:
            try:
                return bool(self._client.set(key, value, ex=ex))
            except Exception as e:
                logger.warning("Redis set error for %s: %s; falling back to memory store", key, e)
        return self._fallback.set(key, value, ex=ex)

    def delete(self, key: str) -> bool:
        if not self._use_fallback and self._client:
            try:
                return bool(self._client.delete(key))
            except Exception as e:
                logger.warning("Redis delete error for %s: %s; falling back to memory store", key, e)
        return self._fallback.delete(key)

    def exists(self, key: str) -> bool:
        if not self._use_fallback and self._client:
            try:
                return bool(self._client.exists(key))
            except Exception as e:
                logger.warning("Redis exists error for %s: %s; falling back to memory store", key, e)
        return self._fallback.exists(key)

    def flushdb(self) -> bool:
        if not self._use_fallback and self._client:
            try:
                self._client.flushdb()
            except Exception:
                pass
        return self._fallback.flushdb()


redis_client = ResilientRedisClient()
