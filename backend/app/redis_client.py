import redis

from app.config import REDIS_URL

_client = None


def get_redis():
    """Shared Redis connection, created on first use."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client
