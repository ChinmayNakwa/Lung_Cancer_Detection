import pytest
from fastapi.testclient import TestClient

from app import api, auth, retrain_lock, tasks
from app.config import RETRAIN_THRESHOLD

client = TestClient(api.app)


class FakeTask:
    id = "task-1"


@pytest.fixture
def admin_headers(monkeypatch):
    monkeypatch.setattr(auth, "ADMIN_USERNAME", "admin")
    monkeypatch.setattr(auth, "ADMIN_PASSWORD", "s3cret")
    monkeypatch.setattr(auth, "JWT_SECRET", "test-secret-" + "x" * 32)
    token, _ = auth.create_access_token("admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def queued(monkeypatch):
    """Record retrain tasks queued by the API instead of sending them to Celery."""
    calls = []

    def delay(**kwargs):
        calls.append(kwargs)
        return FakeTask()

    monkeypatch.setattr(api.retrain_model, "delay", delay)
    monkeypatch.setattr(api, "count_unused_predictions", lambda: RETRAIN_THRESHOLD)
    return calls


def test_lock_is_exclusive_until_released():
    token = retrain_lock.acquire()
    assert token
    assert retrain_lock.acquire() is None

    retrain_lock.release(token)
    assert retrain_lock.acquire()


def test_release_with_stale_token_keeps_newer_lock():
    token = retrain_lock.acquire()
    retrain_lock.release("stale-token")
    assert retrain_lock.acquire() is None
    retrain_lock.release(token)


def test_manual_retrain_is_not_queued_twice(admin_headers, queued):
    first = client.post("/retrain", headers=admin_headers).json()
    second = client.post("/retrain", headers=admin_headers).json()

    assert first["status"] == "triggered"
    assert second["status"] == "skipped"
    assert second["reason"] == "already_running"
    assert len(queued) == 1
    assert queued[0]["lock_token"]


def test_reviews_over_threshold_queue_one_retrain(admin_headers, queued, monkeypatch):
    monkeypatch.setattr(api, "correct_prediction", lambda *args: True)

    for prediction_id in (1, 2):
        response = client.put(
            f"/correct/{prediction_id}",
            headers=admin_headers,
            json={"corrected_class": "benign"},
        )
        assert response.status_code == 200

    assert len(queued) == 1


def test_lock_is_released_when_queuing_fails(admin_headers, monkeypatch):
    def delay(**kwargs):
        raise ConnectionError("broker down")

    monkeypatch.setattr(api.retrain_model, "delay", delay)
    monkeypatch.setattr(api, "count_unused_predictions", lambda: RETRAIN_THRESHOLD)

    with pytest.raises(ConnectionError):
        client.post("/retrain", headers=admin_headers)
    assert retrain_lock.acquire()


def test_task_releases_lock_when_done(monkeypatch):
    monkeypatch.setattr(tasks, "_retrain", lambda: {"status": "success"})
    token = retrain_lock.acquire()

    assert tasks.retrain_model(lock_token=token) == {"status": "success"}
    assert retrain_lock.acquire()


def test_task_without_lock_skips_while_another_run_holds_it(monkeypatch):
    monkeypatch.setattr(tasks, "_retrain", lambda: pytest.fail("should not train"))
    retrain_lock.acquire()

    result = tasks.retrain_model()
    assert result == {"status": "skipped", "reason": "already_running"}
