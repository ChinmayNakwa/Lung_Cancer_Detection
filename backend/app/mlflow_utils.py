import mlflow
import mlflow.keras
import tensorflow as tf
from pathlib import Path

import logging

from app.config import MODEL_DIR, IMG_SIZE

logger = logging.getLogger(__name__)

MODEL_PATH = Path("models") / "EfficientNetB4_Lung_Cancer_prediciton.keras"
EXPERIMENT_NAME = "lung-cancer-models"
REGISTERED_MODEL_NAME = "LungCancerClassifier"

def sync_model_to_mlflow(class_names: list):
    """Log existing trained model to MLflow (idempotent)."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="initial_model_sync"):
        model = tf.keras.models.load_model(MODEL_PATH)

        # Log metadata 
        mlflow.log_param("framework", "tensorflow")
        mlflow.log_param("architecture", "EfficientNetB4")
        mlflow.log_param("img_size", IMG_SIZE)
        mlflow.log_param("num_classes", len(class_names))
        mlflow.log_param("class_order", class_names)
        mlflow.log_param("preprocessing", "resize + normalize(/255)")

        mlflow.keras.log_model(
            model,
            artifact_path="model",
            registered_model_name=REGISTERED_MODEL_NAME
        )

    logger.info("✅ Model synced to MLflow successfully")
