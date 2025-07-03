from fastapi.testclient import TestClient
from app.api import app
from pathlib import Path 

client = TestClient(app)


test_image_path = Path("data") / "sample_images" / "Screenshot 2025-07-03 020154.png"

CLASS_NAMES = ['benign', 'adenocarcinoma', 'squamous_carcinoma']

def test_read_root():
    """
    Test the health check endpoint (/). It should return a 200 OK status
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Welcome to the Lung Cancer Detection API!"
    }

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