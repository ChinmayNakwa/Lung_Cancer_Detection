from pathlib import Path

import psycopg2
import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.config import BASE_MODEL_PATH, CLASS_NAMES, DATABASE_URL

client = TestClient(app)


test_image_path = Path("data") / "sample_images" / "Screenshot 2025-07-03 020154.png"


def _database_available():
    try:
        psycopg2.connect(DATABASE_URL, connect_timeout=2).close()
        return True
    except Exception:
        return False


# The model file is not in the repo and CI has no Postgres, so skip there
requires_model_and_db = pytest.mark.skipif(
    not BASE_MODEL_PATH.exists() or not _database_available(),
    reason="needs the model file and a reachable Postgres",
)


def test_read_root():
    """
    Test the health check endpoint (/). It should return a 200 OK status
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Welcome to the Lung Cancer Detection API!",
        "classes": CLASS_NAMES
    }

@requires_model_and_db
def test_predict_success():
    """
    Test the /predict endpoint with a valid image file
    It should return a 200 OK status and a valid prediction
    """

    with open(test_image_path, "rb") as f:
        response = client.post("/predict", files={"file": ("test_image.jpg", f, "image/jpeg")})

    assert response.status_code == 200

    data = response.json()
    assert "predicted_class" in data
    assert "confidence" in data
    assert data["predicted_class"] in CLASS_NAMES

def test_predict_invalid_file():
    """
    Test the /predict endpoint with a non-image file (e.g., a text file).
    It should return a 400 Bad Request error.
    """

    files = {"file": ("test.txt", b"This is not an image", "text/plain")}

    response = client.post("/predict", files=files)

    assert response.status_code == 400

    assert response.json() == {"detail": "File provided is not an image."}

def test_predict_undecodable_image():
    """
    An upload labelled as an image that cannot be decoded should be a 400,
    not a server error.
    """
    files = {"file": ("scan.png", b"not really a png", "image/png")}

    response = client.post("/predict", files=files)

    assert response.status_code == 400
    assert response.json() == {"detail": "File could not be read as an image."}

@pytest.mark.parametrize("method, path", [
    ("PUT", "/correct/1"),
    ("POST", "/retrain"),
    ("POST", "/models/1/activate"),
    ("POST", "/models/sync"),
])
def test_admin_endpoints_require_token(method, path):
    """
    Endpoints that change labels or models must reject unauthenticated calls.
    """
    response = client.request(method, path, json={"corrected_class": "benign"})

    assert response.status_code == 401
