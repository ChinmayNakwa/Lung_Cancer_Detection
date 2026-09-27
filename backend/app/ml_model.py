import tensorflow as tf
from PIL import Image
import numpy as np
from io import BytesIO
from pathlib import Path
import logging
from app.config import BASE_MODEL_PATH, IMG_SIZE, CLASS_NAMES, model_path
from app.database import get_active_model

logger = logging.getLogger(__name__)


class ModelNotLoadedError(RuntimeError):
    """No model could be loaded, so predictions are unavailable."""


class InvalidImageError(ValueError):
    """The uploaded bytes could not be decoded as an image."""


class ModelManager:
    """Serves whichever model version is marked active in the database.

    Retraining runs in the Celery worker, a separate process, so the API
    checks the active version before each prediction and reloads when it
    has changed.
    """

    def __init__(self):
        self.model = None
        self.version = None  # None means the base model

    def _load(self, path):
        """Load model from path, or return None."""
        try:
            if not Path(path).exists():
                logger.warning(f"Model file not found at {path}")
                return None
            model = tf.keras.models.load_model(path)
            logger.info(f"Model loaded from {path}")
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None

    def sync_active_model(self):
        """Load the active model version if it differs from the loaded one."""
        active = get_active_model()
        version = active["version"] if active else None
        if self.model is not None and version == self.version:
            return

        self.version = version
        self.model = self._load(model_path(version))
        if self.model is None and version is not None:
            logger.warning(f"Model v{version} could not be loaded; falling back to base model")
            self.model = self._load(BASE_MODEL_PATH)

    def predict(self, image_bytes: bytes):
        """Predict from image bytes - matches training preprocessing exactly.

        Raises InvalidImageError for undecodable input and
        ModelNotLoadedError when no model is available.
        """
        # Decode first so bad input is reported as such even without a model
        try:
            img = Image.open(BytesIO(image_bytes)).convert('RGB')
        except Exception as e:
            raise InvalidImageError(f"Could not decode image: {e}") from e

        try:
            self.sync_active_model()
        except Exception as e:
            logger.error(f"Could not check active model version: {e}")

        if self.model is None:
            raise ModelNotLoadedError("Model is not loaded")

        img_resized = img.resize((IMG_SIZE, IMG_SIZE))
        img_array = tf.keras.preprocessing.image.img_to_array(img_resized)
        img_array = np.expand_dims(img_array, axis=0)
        # img_array = img_array / 255.0

        # Make prediction
        predictions = self.model.predict(img_array)
        scores = predictions[0]
        predicted_class = CLASS_NAMES[np.argmax(scores)]
        confidence = 100 * np.max(scores)

        # Return all class probabilities for debugging
        all_predictions = {CLASS_NAMES[i]: float(scores[i] * 100) for i in range(len(CLASS_NAMES))}

        return {
            "predicted_class": predicted_class,
            "confidence": f"{confidence:.2f}%",
            "all_predictions": all_predictions
        }

# Global model manager
model_manager = ModelManager()

def predict(image_bytes: bytes):
    """Predict function for API."""
    return model_manager.predict(image_bytes)

def sync_active_model():
    """Load the database's active model version into the API."""
    model_manager.sync_active_model()
