import pytest

from app import redis_client


class FakeRedis:
    """In-memory stand-in for the few Redis commands the app uses."""

    def __init__(self):
        self.data = {}
        self.ttls = {}

    def get(self, key):
        return self.data.get(key)

    def incr(self, key):
        self.data[key] = str(int(self.data.get(key, 0)) + 1)
        return int(self.data[key])

    def expire(self, key, seconds, nx=False):
        if nx and key in self.ttls:
            return False
        self.ttls[key] = seconds
        return True

    def ttl(self, key):
        return self.ttls.get(key, -1)

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value
        return True

    def delete(self, key):
        self.ttls.pop(key, None)
        return 1 if self.data.pop(key, None) is not None else 0

    def eval(self, script, numkeys, key, token):
        # Only the retrain lock's compare-and-delete script is used
        if self.data.get(key) == token:
            return self.delete(key)
        return 0


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    """Keep tests off a real Redis server."""
    fake = FakeRedis()
    monkeypatch.setattr(redis_client, "_client", fake)
    return fake
