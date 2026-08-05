import json
from typing import Any, Dict, Optional
import redis
from flask import current_app

_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client connection"""
    global _client
    
    if _client is not None:
        return _client
    
    try:
        redis_url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
        _client = redis.from_url(redis_url, decode_responses=True)
        _client.ping()  # Test connection
        print("✅ Redis connected successfully")
        return _client
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}. Using fallback (no caching)")
        _client = None
        return None


def cache_get_json(key: str) -> Optional[Dict[str, Any]]:
    """Get JSON value from cache"""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if not value:
            return None
        return json.loads(value)
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


def cache_set_json(key: str, value: Dict[str, Any], ttl: int = 60) -> bool:
    """Set JSON value in cache with TTL"""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


def cache_clear_pattern(pattern: str) -> int:
    """Clear all keys matching pattern"""
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache clear pattern error: {e}")
        return 0


class SimpleCache:
    """Fallback in-memory cache when Redis is not available"""
    def __init__(self):
        self._cache = {}
    
    def get(self, key):
        import time
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                return value
            del self._cache[key]
        return None
    
    def set(self, key, value, ttl=60):
        import time
        self._cache[key] = (value, time.time() + ttl)
    
    def delete(self, key):
        if key in self._cache:
            del self._cache[key]


# Use simple cache if Redis is not available
_fallback_cache = SimpleCache()


def cache_get_simple(key: str) -> Optional[Any]:
    """Get from simple fallback cache"""
    return _fallback_cache.get(key)


def cache_set_simple(key: str, value: Any, ttl: int = 60) -> None:
    """Set in simple fallback cache"""
    _fallback_cache.set(key, value, ttl)