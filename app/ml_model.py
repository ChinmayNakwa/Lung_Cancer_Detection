import tensorflow as tf
from PIL import Image
import numpy as np
from io import BytesIO
from typing import Dict
from pathlib import Path #

MODEL_PATH = Path("models") / "EfficientNetB4_Lung_Cancer_prediciton.keras"

IMG_SIZE = 256

CLASS_NAMES = ['benign', 'adenocarcinoma', 'squamous_carcinoma']

try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print(f"Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

def predict(image_bytes: bytes) -> Dict:
    """
    Takes image bytes as input, preprocesses the image,
    and returns a dictionary with the predicted class and confidence score.
    """

    if model is None:
        return {"error": "Model is not loaded"}
    
    try:
        img = Image.open(BytesIO(image_bytes)).convert('RGB')

        img_resized = img.resize((IMG_SIZE, IMG_SIZE))
        img_array = tf.keras.preprocessing.image.img_to_array(img_resized)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = img_array / 255.0

        predictions = model.predict(img_array)

        scores = predictions[0]
        predicted_class = CLASS_NAMES[np.argmax(scores)]
        confidence = 100 * np.max(scores)

        return {
            "predicted_class": predicted_class,
            "confidence": f"{confidence: .2f}%"
        }
    
    except Exception as e:
        return {"error": f"Prediction failed: {e}"}
    