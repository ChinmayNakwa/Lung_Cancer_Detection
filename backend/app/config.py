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

# MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")

# Model
MODEL_DIR = Path("models")
MODEL_NAME = "lung_cancer_model"
IMG_SIZE = int(os.getenv("IMG_SIZE", "256"))
CLASS_NAMES = ['adenocarcinoma', 'benign', 'squamous_carcinoma']

# Training
RETRAIN_THRESHOLD = int(os.getenv("RETRAIN_THRESHOLD", "50"))
EPOCHS = int(os.getenv("EPOCHS", "10"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "16"))