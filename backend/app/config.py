import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Database
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Redis
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Auth: protected endpoints reject all requests until these are set
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))
# Failed logins allowed per client IP before /login is blocked for the window
LOGIN_MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "900"))

# Browser origins allowed to call the API (comma-separated)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")

# Model
MODEL_DIR = Path("models")
MODEL_NAME = "lung_cancer_model"
BASE_MODEL_PATH = MODEL_DIR / "EfficientNetB4_Lung_Cancer_prediciton.keras"


def model_path(version=None):
    """Saved model file for a version; None means the original base model."""
    return BASE_MODEL_PATH if version is None else MODEL_DIR / f"model_v{version}.keras"


IMG_SIZE = int(os.getenv("IMG_SIZE", "256"))
# Largest image /predict accepts
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
CLASS_NAMES = ['adenocarcinoma', 'benign', 'squamous_carcinoma']

# Training
RETRAIN_THRESHOLD = int(os.getenv("RETRAIN_THRESHOLD", "50"))
EPOCHS = int(os.getenv("EPOCHS", "10"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "16"))
# Seconds before a retraining lock left by a crashed run expires
RETRAIN_LOCK_TIMEOUT = int(os.getenv("RETRAIN_LOCK_TIMEOUT", "7200"))
# Share of reviewed samples held out to evaluate each retrained model
HOLDOUT_FRACTION = float(os.getenv("HOLDOUT_FRACTION", "0.2"))
# Fewest samples to hold out, so accuracy is not judged on a handful of images
MIN_HOLDOUT_SAMPLES = int(os.getenv("MIN_HOLDOUT_SAMPLES", "20"))