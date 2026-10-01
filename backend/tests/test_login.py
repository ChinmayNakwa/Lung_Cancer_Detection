import pytest
import redis
from fastapi.testclient import TestClient

from app import api, auth, redis_client
from app.config import LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS

client = TestClient(api.app)

GOOD = {"username": "admin", "password": "s3cret"}
BAD = {"username": "admin", "password": "wrong"}


@pytest.fixture(autouse=True)
def configure_auth(monkeypatch):
    monkeypatch.setattr(auth, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(auth, "ADMIN_PASSWORD", "s3cret")
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret-" + "x" * 32)


def test_login_returns_token():
    response = client.post("/login", json=GOOD)

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_is_blocked_after_too_many_failures():
    for _ in range(LOGIN_MAX_FAILURES):
        assert client.post("/login", json=BAD).status_code == 401

    # Even the right password is refused until the window expires
    response = client.post("/login", json=GOOD)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(LOGIN_WINDOW_SECONDS)


def test_successful_login_resets_failure_count():
    for _ in range(LOGIN_MAX_FAILURES - 1):
        client.post("/login", json=BAD)
    assert client.post("/login", json=GOOD).status_code == 200

    assert client.post("/login", json=BAD).status_code == 401


def test_login_still_works_when_redis_is_down(monkeypatch):
    class DownRedis:
        def __getattr__(self, name):
            def fail(*args, **kwargs):
                raise redis.ConnectionError("redis down")
            return fail

    monkeypatch.setattr(redis_client, "_client", DownRedis())

    assert client.post("/login", json=BAD).status_code == 401
    assert client.post("/login", json=GOOD).status_code == 200
