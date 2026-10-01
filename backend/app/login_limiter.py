import logging

import redis

from app import redis_client
from app.config import LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS

logger = logging.getLogger(__name__)


def _key(client_ip):
    return f"lung_cancer:login_failures:{client_ip}"


def retry_after(client_ip):
    """Seconds until this IP may try to log in again; 0 if it is not blocked."""
    try:
        r = redis_client.get_redis()
        failures = r.get(_key(client_ip))
        if failures is None or int(failures) < LOGIN_MAX_FAILURES:
            return 0
        return max(r.ttl(_key(client_ip)), 1)
    except redis.RedisError as e:
        # Fail open so admins can still log in while Redis is down
        logger.warning(f"Login rate limit check skipped: {e}")
        return 0


def record_failure(client_ip):
    """Count a failed login; the window starts at the first failure."""
    try:
        r = redis_client.get_redis()
        r.incr(_key(client_ip))
        r.expire(_key(client_ip), LOGIN_WINDOW_SECONDS, nx=True)
    except redis.RedisError as e:
        logger.warning(f"Could not record failed login: {e}")


def reset(client_ip):
    """Clear the failure count after a successful login."""
    try:
        redis_client.get_redis().delete(_key(client_ip))
    except redis.RedisError as e:
        logger.warning(f"Could not reset failed logins: {e}")
