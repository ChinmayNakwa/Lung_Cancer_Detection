import random
import shutil
from pathlib import Path

# Source dataset
BASE_DIR = Path(r"Val")

# Output directory
OUT_DIR = Path(r"selected_50")

SPLIT = {
    "benign": 100,
    "adenocarcinoma": 100,
    "squamous_carcinoma": 100,
}

IMAGE_EXTS = (".jpg", ".jpeg", ".png")

OUT_DIR.mkdir(exist_ok=True)

for class_name, count in SPLIT.items():
    src_dir = BASE_DIR / class_name
    dst_dir = OUT_DIR / class_name
    dst_dir.mkdir(parents=True, exist_ok=True)

    images = [p for p in src_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS]

    if len(images) < count:
        raise ValueError(f"Not enough images in {class_name}")

    selected = random.sample(images, count)

    for img in selected:
        shutil.copy(img, dst_dir / img.name)

    print(f"Copied {count} images from {class_name}")

print("✅ Image selection complete")
