import uuid

from app import redis_client
from app.config import RETRAIN_LOCK_TIMEOUT

# Held from the moment a retrain is queued until it finishes, so only one
# run is ever queued or running at a time
LOCK_KEY = "lung_cancer:retrain_lock"

# Delete the key only if it still holds our token, so a run whose lock
# expired cannot release a lock taken by a newer run
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


def acquire():
    """Take the lock; return its token, or None if a run already holds it."""
    token = uuid.uuid4().hex
    if redis_client.get_redis().set(LOCK_KEY, token, nx=True, ex=RETRAIN_LOCK_TIMEOUT):
        return token
    return None


def release(token):
    """Release the lock if it is still held with this token."""
    redis_client.get_redis().eval(_RELEASE_SCRIPT, 1, LOCK_KEY, token)
