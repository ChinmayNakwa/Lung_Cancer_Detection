import pytest

from app import redis_client


class FakeRedis:
    """In-memory stand-in for the few Redis commands the app uses."""

    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value
        return True

    def delete(self, key):
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
