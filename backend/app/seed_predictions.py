import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load same env file as backend
load_dotenv()

# =====================
# DATABASE CONFIG (HOST)
# =====================
DB_CONFIG = {
    "host": "localhost",                
    "port": 5435,
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# =====================
# IMAGE CONFIG
# =====================
BASE_DIR = Path(r"selected_50")
IMAGE_EXTS = (".jpg", ".jpeg", ".png")

CLASS_NAMES = ['adenocarcinoma', 'benign', 'squamous_carcinoma']

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total = 0

    for class_name in CLASS_NAMES:
        class_dir = BASE_DIR / class_name

        if not class_dir.exists():
            print(f"⚠️ Folder not found: {class_dir}")
            continue

        for img_path in class_dir.iterdir():
            if img_path.suffix.lower() not in IMAGE_EXTS:
                continue

            with open(img_path, "rb") as f:
                image_bytes = f.read()

            cur.execute(
                """
                INSERT INTO predictions
                (filename, image_data, predicted_class, confidence, used_for_training)
                VALUES (%s, %s, %s, %s, FALSE)
                """,
                (img_path.name, psycopg2.Binary(image_bytes), class_name, "1.0")
            )

            total += 1

        print(f"✅ Inserted images for class: {class_name}")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n🎉 Done — {total} images inserted into DB")

if __name__ == "__main__":
    main()
