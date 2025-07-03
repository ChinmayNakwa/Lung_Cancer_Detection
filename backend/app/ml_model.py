import tensorflow as tf
from PIL import Image
import numpy as np
from io import BytesIO
from pathlib import Path
import logging
from app.config import MODEL_DIR, IMG_SIZE, CLASS_NAMES

logger = logging.getLogger(__name__)

MODEL_PATH = Path("models") / "EfficientNetB4_Lung_Cancer_prediciton.keras"

class ModelManager:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self, model_path=None):
        """Load model from path."""
        path = model_path or MODEL_PATH
        try:
            if not Path(path).exists():
                logger.warning(f"Model file not found at {path}")
                self.model = None
                return
            self.model = tf.keras.models.load_model(path)
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
    
    def predict(self, image_bytes: bytes):
        """Predict from image bytes - matches training preprocessing exactly."""
        if self.model is None:
            return {"error": "Model is not loaded"}
        
        try:
            img = Image.open(BytesIO(image_bytes)).convert('RGB')
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
        except Exception as e:
            return {"error": f"Prediction failed: {e}"}

# Global model manager
model_manager = ModelManager()

def predict(image_bytes: bytes):
    """Predict function for API."""
    return model_manager.predict(image_bytes)

def reload_model(model_path=None):
    """Reload model."""
    model_manager.load_model(model_path)