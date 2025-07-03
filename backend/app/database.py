import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255),
            image_data BYTEA NOT NULL,
            predicted_class VARCHAR(50),
            corrected_class VARCHAR(50),
            confidence VARCHAR(20),
            used_for_training BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id SERIAL PRIMARY KEY,
            version INTEGER UNIQUE NOT NULL,
            mlflow_run_id VARCHAR(255),
            is_active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Database initialized successfully")

def save_prediction(filename: str, image_bytes: bytes, predicted_class: str, confidence: str):
    """Save image and prediction to database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO predictions (filename, image_data, predicted_class, confidence)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (filename, psycopg2.Binary(image_bytes), predicted_class, confidence)
    )
    
    prediction_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    
    return prediction_id

def correct_prediction(prediction_id: int, corrected_class: str):
    """Update the corrected class for a prediction."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE predictions SET corrected_class = %s WHERE id = %s",
        (corrected_class, prediction_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def get_unused_predictions(limit: int):
    """Get predictions not used for training."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        """
        SELECT id, image_data, 
               COALESCE(corrected_class, predicted_class) as label
        FROM predictions 
        WHERE used_for_training = FALSE 
        ORDER BY created_at DESC 
        LIMIT %s
        """,
        (limit,)
    )
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return results

def mark_as_trained(prediction_ids: list):
    """Mark predictions as used for training."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE predictions SET used_for_training = TRUE WHERE id = ANY(%s)",
        (prediction_ids,)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def count_unused_predictions():
    """Count predictions not used for training."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE used_for_training = FALSE")
    count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return count

def save_model_version(version: int, mlflow_run_id: str, is_active: bool = True):
    """Save model version info."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_active:
        cursor.execute("UPDATE models SET is_active = FALSE")
    
    cursor.execute(
        """
        INSERT INTO models (version, mlflow_run_id, is_active)
        VALUES (%s, %s, %s)
        """,
        (version, mlflow_run_id, is_active)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def get_all_models():
    """Get all model versions."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM models ORDER BY version DESC")
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return results

def activate_model(version: int):
    """Activate a specific model version."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE models SET is_active = FALSE")
    cursor.execute("UPDATE models SET is_active = TRUE WHERE version = %s", (version,))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_active_model():
    """Get the active model version."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM models WHERE is_active = TRUE LIMIT 1")
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result