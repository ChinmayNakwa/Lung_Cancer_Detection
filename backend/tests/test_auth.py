from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import auth

SECRET = "test-secret-" + "x" * 32


@pytest.fixture(autouse=True)
def configure_auth(monkeypatch):
    monkeypatch.setattr(auth, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(auth, "ADMIN_PASSWORD", "s3cret")
    monkeypatch.setattr(auth, "JWT_SECRET", SECRET)


@pytest.fixture
def client():
    """Minimal app with one protected route, so no model or database is needed."""
    app = FastAPI()

    @app.get("/protected")
    def protected(user: str = Depends(auth.require_admin)):
        return {"user": user}

    return TestClient(app)


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_verify_credentials():
    assert auth.verify_credentials("admin", "s3cret")
    assert not auth.verify_credentials("admin", "wrong")
    assert not auth.verify_credentials("someone", "s3cret")


def test_verify_credentials_fails_closed_when_unconfigured(monkeypatch):
    monkeypatch.setattr(auth, "ADMIN_PASSWORD", None)
    assert not auth.verify_credentials("admin", "s3cret")


def test_valid_token_is_accepted(client):
    token, expires = auth.create_access_token("admin")
    assert expires > datetime.now(timezone.utc)

    response = client.get("/protected", headers=bearer(token))
    assert response.status_code == 200
    assert response.json() == {"user": "admin"}


def test_missing_token_is_rejected(client):
    assert client.get("/protected").status_code == 401


def test_malformed_token_is_rejected(client):
    assert client.get("/protected", headers=bearer("garbage")).status_code == 401


def test_token_with_wrong_secret_is_rejected(client):
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({"sub": "admin", "exp": expires}, "other-secret-" + "y" * 32, algorithm="HS256")
    assert client.get("/protected", headers=bearer(token)).status_code == 401


def test_expired_token_is_rejected(client):
    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    token = jwt.encode({"sub": "admin", "exp": expired}, SECRET, algorithm="HS256")
    assert client.get("/protected", headers=bearer(token)).status_code == 401


def test_token_without_expiry_is_rejected(client):
    token = jwt.encode({"sub": "admin"}, SECRET, algorithm="HS256")
    assert client.get("/protected", headers=bearer(token)).status_code == 401


def test_all_tokens_rejected_when_unconfigured(client, monkeypatch):
    token, _ = auth.create_access_token("admin")
    monkeypatch.setattr(auth, "JWT_SECRET", None)
    assert client.get("/protected", headers=bearer(token)).status_code == 401
