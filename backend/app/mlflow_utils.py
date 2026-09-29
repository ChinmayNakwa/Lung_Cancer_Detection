import mlflow
import mlflow.keras
import tensorflow as tf

import logging

from app.config import BASE_MODEL_PATH, IMG_SIZE

logger = logging.getLogger(__name__)

EXPERIMENT_NAME = "lung-cancer-models"
REGISTERED_MODEL_NAME = "LungCancerClassifier"
SYNC_RUN_NAME = "initial_model_sync"

def sync_model_to_mlflow(class_names: list):
    """Log the base model to MLflow once; later calls are no-ops.

    Returns (run_id, created), where created is False if a finished sync
    run already existed.
    """

    if not BASE_MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {BASE_MODEL_PATH}")

    experiment = mlflow.set_experiment(EXPERIMENT_NAME)

    # A failed earlier sync is not FINISHED, so it gets retried
    existing = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f"tags.sync_type = '{SYNC_RUN_NAME}' and attributes.status = 'FINISHED'",
        max_results=1,
        output_format="list",
    )
    if existing:
        run_id = existing[0].info.run_id
        logger.info(f"Model already synced to MLflow in run {run_id}")
        return run_id, False

    with mlflow.start_run(run_name=SYNC_RUN_NAME) as run:
        mlflow.set_tag("sync_type", SYNC_RUN_NAME)
        model = tf.keras.models.load_model(BASE_MODEL_PATH)

        # Log metadata
        mlflow.log_param("framework", "tensorflow")
        mlflow.log_param("architecture", "EfficientNetB4")
        mlflow.log_param("img_size", IMG_SIZE)
        mlflow.log_param("num_classes", len(class_names))
        mlflow.log_param("class_order", class_names)
        # EfficientNet rescales internally, so inputs stay in the 0-255 range
        mlflow.log_param("preprocessing", "resize only (raw 0-255 pixels)")

        mlflow.keras.log_model(
            model,
            artifact_path="model",
            registered_model_name=REGISTERED_MODEL_NAME
        )

    logger.info("✅ Model synced to MLflow successfully")
    return run.info.run_id, True
