import os
import time
import logging
from pathlib import Path
from io import BytesIO

import tensorflow as tf
import numpy as np
import mlflow
import matplotlib.pyplot as plt
import seaborn as sns

from PIL import Image
from sklearn.metrics import confusion_matrix, classification_report

from app.celery_app import celery_app
from app.database import (
    get_unused_predictions,
    mark_as_trained,
    save_model_version,
    get_all_models,
)
from app.config import (
    MLFLOW_TRACKING_URI,
    MODEL_NAME,
    IMG_SIZE,
    CLASS_NAMES,
    EPOCHS,
    BATCH_SIZE,
    RETRAIN_THRESHOLD,
)
from app.ml_model import reload_model

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Utility: Training Curves (FILE-BASED, MLflow-safe)
# ------------------------------------------------------------------
def log_training_curves(history, save_path="/tmp/training_curves.png"):
    epochs_range = range(len(history.history["loss"]))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

    ax1.plot(epochs_range, history.history["loss"], label="Train Loss")
    if "val_loss" in history.history:
        ax1.plot(epochs_range, history.history["val_loss"], label="Val Loss")
    ax1.set_title("Loss")
    ax1.legend()
    ax1.grid(True)

    ax2.plot(epochs_range, history.history["accuracy"], label="Train Accuracy")
    if "val_accuracy" in history.history:
        ax2.plot(epochs_range, history.history["val_accuracy"], label="Val Accuracy")
    ax2.set_title("Accuracy")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

    mlflow.log_artifact(save_path)

    # Per-epoch metrics
    for epoch in epochs_range:
        mlflow.log_metric("epoch_loss", history.history["loss"][epoch], step=epoch)
        mlflow.log_metric(
            "epoch_accuracy", history.history["accuracy"][epoch], step=epoch
        )


# ------------------------------------------------------------------
# Utility: Evaluation Metrics + Confusion Matrix
# ------------------------------------------------------------------
def log_evaluation_metrics(model, X, y, save_path="/tmp/confusion_matrix.png"):
    y_true = np.argmax(y, axis=1)
    y_pred = model.predict(X)
    y_pred_cls = np.argmax(y_pred, axis=1)

    cm = confusion_matrix(y_true, y_pred_cls)

    fig, ax = plt.subplots(figsize=(6, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

    mlflow.log_artifact(save_path)

    report = classification_report(
        y_true, y_pred_cls, target_names=CLASS_NAMES, output_dict=True
    )

    for cls_name, metrics in report.items():
        if isinstance(metrics, dict):
            mlflow.log_metric(f"{cls_name}_precision", metrics["precision"])
            mlflow.log_metric(f"{cls_name}_recall", metrics["recall"])
            mlflow.log_metric(f"{cls_name}_f1", metrics["f1-score"])


# ------------------------------------------------------------------
# Celery Task: Retraining
# ------------------------------------------------------------------
@celery_app.task(name="app.tasks.retrain_model")
def retrain_model():
    try:
        logger.info("Starting model retraining")

        predictions = get_unused_predictions(RETRAIN_THRESHOLD)
        if len(predictions) < RETRAIN_THRESHOLD:
            return {"status": "skipped", "reason": "insufficient_data"}

        X_train, y_train, prediction_ids = [], [], []

        for pred in predictions:
            img = Image.open(BytesIO(pred["image_data"])).convert("RGB")
            img = img.resize((IMG_SIZE, IMG_SIZE))
            arr = tf.keras.preprocessing.image.img_to_array(img)
            arr = tf.keras.applications.efficientnet.preprocess_input(arr)

            X_train.append(arr)
            y_train.append(CLASS_NAMES.index(pred["label"]))
            prediction_ids.append(pred["id"])

        X_train = np.array(X_train)
        y_train = tf.keras.utils.to_categorical(
            y_train, num_classes=len(CLASS_NAMES)
        )

        base_model_path = Path(
            "/app/models/EfficientNetB4_Lung_Cancer_prediciton.keras"
        )
        if not base_model_path.exists():
            raise FileNotFoundError("Base model not found")

        model = tf.keras.models.load_model(base_model_path)

        # Fine-tuning strategy
        model.trainable = True
        for layer in model.layers[:-5]:
            layer.trainable = False

        model.compile(
            optimizer=tf.keras.optimizers.Adam(1e-4),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )

        all_models = get_all_models()
        next_version = max([m["version"] for m in all_models], default=0) + 1

        # MLflow (runtime-safe)
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment("lung-cancer-detection")

        with mlflow.start_run(run_name=f"retrain_v{next_version}") as run:
            start_time = time.time()

            # ---------------- Params ----------------
            mlflow.log_params({
                "samples": len(X_train),
                "epochs": EPOCHS,
                "batch_size": BATCH_SIZE,
                "learning_rate": 1e-4,
                "optimizer": "Adam",
                "architecture": "EfficientNetB4",
                "img_size": IMG_SIZE,
                "num_classes": len(CLASS_NAMES),
                "class_names": ",".join(CLASS_NAMES),
                "retrain_threshold": RETRAIN_THRESHOLD,
            })

            # ---------------- Data Distribution ----------------
            unique, counts = np.unique(
                np.argmax(y_train, axis=1), return_counts=True
            )
            for cls, cnt in zip(unique, counts):
                mlflow.log_metric(f"class_count_{CLASS_NAMES[cls]}", cnt)

            mlflow.log_param("training_data_hash", hash(X_train.tobytes()))

            # ---------------- Training ----------------
            history = model.fit(
                X_train,
                y_train,
                epochs=EPOCHS,
                batch_size=BATCH_SIZE,
                shuffle=True,
                verbose=1,
            )

            training_time = time.time() - start_time
            mlflow.log_metric("training_time_sec", training_time)

            log_training_curves(history)

            # ---------------- Final Metrics ----------------
            mlflow.log_metrics({
                "final_loss": history.history["loss"][-1],
                "final_accuracy": history.history["accuracy"][-1],
                "total_params": model.count_params(),
                "trainable_params": int(
                    sum(tf.size(w).numpy() for w in model.trainable_weights)
                ),
            })

            with mlflow.start_run(run_name=f"eval_v{next_version}", nested=True):
                log_evaluation_metrics(model, X_train, y_train)
                
            mlflow.tensorflow.log_model(model, artifact_path="model")

            run_id = mlflow.active_run().info.run_id

            # Model Registry (safe)
            try:
                mlflow.register_model(
                    f"runs:/{run_id}/model",
                    MODEL_NAME
                )
            except Exception as e:
                logger.warning(f"Model registration skipped: {e}")

        # ---------------- Local Save + Reload ----------------
        local_model_path = Path(f"/app/models/model_v{next_version}.keras")
        model.save(local_model_path)

        save_model_version(next_version, run_id, is_active=True)
        mark_as_trained(prediction_ids)
        reload_model(local_model_path)

        logger.info(f"Model v{next_version} retrained successfully")

        return {
            "status": "success",
            "version": next_version,
            "run_id": run_id,
        }

    except Exception as e:
        logger.exception("Retraining failed")
        return {"status": "error", "error": str(e)}
