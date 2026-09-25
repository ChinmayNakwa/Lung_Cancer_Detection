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
from sklearn.model_selection import train_test_split

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
    HOLDOUT_FRACTION,
)
from app.ml_model import reload_model

logger = logging.getLogger(__name__)

# Number of trailing backbone layers left trainable (matches the notebook)
FINE_TUNE_LAYERS = 10
LEARNING_RATE = 1e-4


# ------------------------------------------------------------------
# Utility: Freeze pretrained backbone for fine-tuning
# ------------------------------------------------------------------
def freeze_backbone(model, trainable_layers=FINE_TUNE_LAYERS):
    """Freeze the EfficientNet backbone except its last few layers.

    The saved model nests the backbone as a single layer
    (input -> augmentation -> efficientnetb4 -> pooling -> output), so
    slicing model.layers never reaches the backbone's own layers.
    """
    model.trainable = True

    # Augmentation is also a nested model; the backbone is the largest one
    backbone = max(
        (l for l in model.layers if isinstance(l, tf.keras.Model)),
        key=lambda l: len(l.layers),
    )
    for layer in backbone.layers[:-trainable_layers]:
        layer.trainable = False

    # BatchNorm stays frozen: small retrain batches would corrupt its weights
    for layer in backbone.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False


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
def split_holdout(labels):
    """Return (train_idx, holdout_idx), stratified by class when possible."""
    indices = np.arange(len(labels))
    try:
        return train_test_split(
            indices, test_size=HOLDOUT_FRACTION, stratify=labels, random_state=42
        )
    except ValueError:
        # A class has too few samples to stratify
        return train_test_split(
            indices, test_size=HOLDOUT_FRACTION, random_state=42
        )


def log_evaluation_metrics(model, X, y, save_path="/tmp/confusion_matrix.png"):
    """Log confusion matrix and per-class metrics; return accuracy."""
    y_true = np.argmax(y, axis=1)
    y_pred = model.predict(X, verbose=0)
    y_pred_cls = np.argmax(y_pred, axis=1)
    class_ids = list(range(len(CLASS_NAMES)))

    cm = confusion_matrix(y_true, y_pred_cls, labels=class_ids)

    fig, ax = plt.subplots(figsize=(6, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

    mlflow.log_artifact(save_path)

    # A small holdout may miss a class, so pin labels and avoid zero-division errors
    report = classification_report(
        y_true,
        y_pred_cls,
        labels=class_ids,
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    for cls_name, metrics in report.items():
        if isinstance(metrics, dict):
            mlflow.log_metric(f"{cls_name}_precision", metrics["precision"])
            mlflow.log_metric(f"{cls_name}_recall", metrics["recall"])
            mlflow.log_metric(f"{cls_name}_f1", metrics["f1-score"])

    accuracy = float(np.mean(y_pred_cls == y_true))
    mlflow.log_metric("holdout_accuracy", accuracy)
    return accuracy


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

        X, labels, prediction_ids = [], [], []

        for pred in predictions:
            img = Image.open(BytesIO(pred["image_data"])).convert("RGB")
            img = img.resize((IMG_SIZE, IMG_SIZE))
            arr = tf.keras.preprocessing.image.img_to_array(img)
            arr = tf.keras.applications.efficientnet.preprocess_input(arr)

            X.append(arr)
            labels.append(CLASS_NAMES.index(pred["label"]))
            prediction_ids.append(pred["id"])

        X = np.array(X)
        y = tf.keras.utils.to_categorical(labels, num_classes=len(CLASS_NAMES))
        prediction_ids = np.array(prediction_ids)

        # Hold out reviewed samples so the new model is judged on unseen data.
        # Holdout rows are not marked as trained and feed a later cycle.
        train_idx, holdout_idx = split_holdout(labels)
        X_train, y_train = X[train_idx], y[train_idx]
        X_holdout, y_holdout = X[holdout_idx], y[holdout_idx]
        train_ids = prediction_ids[train_idx].tolist()

        base_model_path = Path(
            "/app/models/EfficientNetB4_Lung_Cancer_prediciton.keras"
        )
        if not base_model_path.exists():
            raise FileNotFoundError("Base model not found")

        model = tf.keras.models.load_model(base_model_path)

        all_models = get_all_models()
        next_version = max([m["version"] for m in all_models], default=0) + 1

        # MLflow (runtime-safe)
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment("lung-cancer-detection")

        with mlflow.start_run(run_name=f"retrain_v{next_version}") as run:
            # ---------------- Baseline (before fine-tuning) ----------------
            with mlflow.start_run(run_name=f"baseline_v{next_version}", nested=True):
                baseline_accuracy = log_evaluation_metrics(model, X_holdout, y_holdout)

            freeze_backbone(model)

            model.compile(
                optimizer=tf.keras.optimizers.Adam(LEARNING_RATE),
                loss="categorical_crossentropy",
                metrics=["accuracy"],
            )

            start_time = time.time()

            # ---------------- Params ----------------
            mlflow.log_params({
                "samples": len(X_train),
                "holdout_samples": len(X_holdout),
                "epochs": EPOCHS,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "fine_tune_layers": FINE_TUNE_LAYERS,
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
                candidate_accuracy = log_evaluation_metrics(model, X_holdout, y_holdout)

            # Only replace the serving model if it is at least as good on unseen data
            activated = candidate_accuracy >= baseline_accuracy
            mlflow.log_metrics({
                "baseline_holdout_accuracy": baseline_accuracy,
                "candidate_holdout_accuracy": candidate_accuracy,
            })
            mlflow.log_param("activated", activated)

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

        save_model_version(next_version, run_id, is_active=activated)
        # Mark rows as used even if the candidate was rejected: otherwise they
        # keep the count over the threshold and every new review would retrain
        # on the same data. The rejected version can still be activated manually.
        mark_as_trained(train_ids)

        if activated:
            reload_model(local_model_path)
            logger.info(f"Model v{next_version} retrained and activated")
        else:
            logger.warning(
                f"Model v{next_version} saved but not activated: holdout accuracy "
                f"{candidate_accuracy:.3f} < baseline {baseline_accuracy:.3f}"
            )

        return {
            "status": "success",
            "version": next_version,
            "run_id": run_id,
            "activated": activated,
            "baseline_holdout_accuracy": baseline_accuracy,
            "candidate_holdout_accuracy": candidate_accuracy,
        }

    except Exception as e:
        logger.exception("Retraining failed")
        return {"status": "error", "error": str(e)}
