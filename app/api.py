from fastapi import FastAPI, File, UploadFile, HTTPException
from app.ml_model import predict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lung Cancer Prediction API",
    description = "An API to classify images using an EfficinetNetB4 Model.",
    version = "1.0.0"
)

@app.get("/")
def read_root():
    """
    A simple health check endpoint.
    """
    return {"status": "ok", "message":"Welcome to the Lung Cancer Detection API!"}

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    """
    Accepts an image file, passes it to the ML model for prediction,
    and the returns the result.
    """

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    try:
        image_bytes = await file.read()

        logger.info("Making a prediction...")
        prediction_result = predict(image_bytes)
        logger.info(f"Prediction result: {prediction_result}")

        if "error" in prediction_result:
            raise HTTPException(status_code=500, detail=prediction_result["error"])
        
        return prediction_result
    
    except Exception as e:
        logger.error(f"An error occurred during prediction: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
    
    