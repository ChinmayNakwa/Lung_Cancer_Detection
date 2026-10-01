from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from app.ml_model import predict, sync_active_model, InvalidImageError, ModelNotLoadedError
from app.mlflow_utils import sync_model_to_mlflow
from app.database import (
    init_db, 
    save_prediction, 
    correct_prediction,
    count_unused_predictions,
    get_all_models,
    activate_model,
    get_active_model
)
from app.tasks import retrain_model
from app import login_limiter, retrain_lock
from app.auth import verify_credentials, create_access_token, require_admin
from app.config import (
    RETRAIN_THRESHOLD,
    CLASS_NAMES,
    CORS_ORIGINS,
    MAX_UPLOAD_MB,
    MAX_UPLOAD_BYTES,
    model_path,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lung Cancer Prediction API",
    description="An API to classify images using an EfficientNetB4 Model with auto-retraining.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CorrectionRequest(BaseModel):
    corrected_class: str

class LoginRequest(BaseModel):
    username: str
    password: str

def queue_retrain():
    """Queue a retraining task; return None if one is already queued or running."""
    token = retrain_lock.acquire()
    if token is None:
        return None
    try:
        return retrain_model.delay(lock_token=token)
    except Exception:
        retrain_lock.release(token)
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    try:
        sync_active_model()
    except Exception as e:
        logger.error(f"Could not load active model at startup: {e}")
    logger.info("API started successfully")

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "ok", 
        "message": "Welcome to the Lung Cancer Detection API!",
        "classes": CLASS_NAMES
    }

@app.post("/login")
def login(request: LoginRequest, http_request: Request):
    """Exchange admin credentials for a bearer token."""
    client_ip = http_request.client.host if http_request.client else "unknown"
    # Checked before the password so a blocked client learns nothing from guesses
    wait = login_limiter.retry_after(client_ip)
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(wait)},
        )
    if not verify_credentials(request.username, request.password):
        login_limiter.record_failure(client_ip)
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    login_limiter.reset(client_ip)
    token, expires = create_access_token(request.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": int(expires.timestamp()),
        "username": request.username
    }

@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    """Upload image for prediction."""
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    # Read one byte past the limit so oversized files are caught without loading them whole
    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.")
    
    try:
        logger.info("Making prediction...")
        prediction_result = predict(image_bytes)
    except InvalidImageError:
        raise HTTPException(status_code=400, detail="File could not be read as an image.")
    except ModelNotLoadedError:
        raise HTTPException(status_code=503, detail="Model is not loaded.")
    except Exception:
        logger.exception("Error during prediction")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
    
    try:
        prediction_id = save_prediction(
            filename=file.filename,
            image_bytes=image_bytes,
            predicted_class=prediction_result["predicted_class"],
            confidence=prediction_result["confidence"]
        )
    except Exception:
        logger.exception("Error saving prediction")
        raise HTTPException(status_code=500, detail="Failed to save prediction.")
    
    prediction_result["id"] = prediction_id
    return prediction_result

@app.put("/correct/{prediction_id}", dependencies=[Depends(require_admin)])
def correct_label(prediction_id: int, request: CorrectionRequest):
    """Correct a prediction label."""
    if request.corrected_class not in CLASS_NAMES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid class. Must be one of: {CLASS_NAMES}"
        )
    
    try:
        if not correct_prediction(prediction_id, request.corrected_class):
            raise HTTPException(status_code=404, detail=f"Prediction {prediction_id} not found.")
        result = {
            "status": "success",
            "prediction_id": prediction_id,
            "corrected_class": request.corrected_class
        }

        # Only reviewed samples count toward retraining, so check here
        unused_count = count_unused_predictions()
        logger.info(f"Reviewed samples awaiting training: {unused_count}")

        if unused_count >= RETRAIN_THRESHOLD and queue_retrain() is not None:
            logger.info(f"Triggering retraining with {unused_count} images")
            result["retraining_triggered"] = True

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error correcting prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to correct prediction.")

@app.post("/retrain", dependencies=[Depends(require_admin)])
def trigger_retrain():
    """Manually trigger model retraining."""
    unused_count = count_unused_predictions()
    
    if unused_count < RETRAIN_THRESHOLD:
        return {
            "status": "skipped",
            "reason": "insufficient_data",
            "unused_count": unused_count,
            "required": RETRAIN_THRESHOLD
        }
    
    task = queue_retrain()
    if task is None:
        return {
            "status": "skipped",
            "reason": "already_running",
            "unused_count": unused_count,
            "required": RETRAIN_THRESHOLD
        }

    return {
        "status": "triggered",
        "task_id": task.id,
        "unused_count": unused_count
    }

@app.get("/models")
def list_models():
    """List all model versions."""
    try:
        models = get_all_models()
        return {
            "models": models,
            "total": len(models)
        }
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models.")

@app.post("/models/{version}/activate", dependencies=[Depends(require_admin)])
def activate_model_version(version: int):
    """Activate a specific model version."""
    try:
        models = get_all_models()
        model_exists = any(m['version'] == version for m in models)
        
        if not model_exists:
            raise HTTPException(status_code=404, detail=f"Model version {version} not found.")
        
        # Check the file before activating so the DB never points at a missing model
        if not model_path(version).exists():
            raise HTTPException(status_code=404, detail=f"Model file not found for version {version}.")
        
        activate_model(version)
        sync_active_model()
        
        return {
            "status": "success",
            "active_version": version,
            "message": f"Model version {version} is now active"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating model: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate model.")

@app.get("/models/active")
def get_current_model():
    """Get currently active model."""
    try:
        active_model = get_active_model()
        if not active_model:
            return {"message": "No active model found"}
        return active_model
    except Exception as e:
        logger.error(f"Error getting active model: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active model.")

@app.get("/stats")
def get_stats():
    """Get system statistics."""
    try:
        unused_count = count_unused_predictions()
        active_model = get_active_model()
        
        return {
            "unused_predictions": unused_count,
            "retrain_threshold": RETRAIN_THRESHOLD,
            "progress_percentage": (unused_count / RETRAIN_THRESHOLD) * 100,
            "active_model_version": active_model['version'] if active_model else None
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats.")
    
@app.post("/models/sync", dependencies=[Depends(require_admin)])
def sync_model():
    """Manually sync the current model to MLflow."""
    try:
        run_id, created = sync_model_to_mlflow(CLASS_NAMES)
        return {
            "status": "success",
            "message": "Model synced to MLflow" if created else "Model already synced to MLflow",
            "model_name": "LungCancerClassifier",
            "run_id": run_id
        }
    except Exception as e:
        logger.error(f"MLflow sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
