# 🫁 Lung Cancer Detection System (Human-in-the-Loop ML)

A full-stack **AI-powered lung cancer detection system** with **online retraining**, **MLflow experiment tracking**, and a **human-in-the-loop learning pipeline**.

This project goes beyond training a deep learning model — it demonstrates how **real-world ML systems evolve**, retrain, and are monitored over time.

---

## ✨ Key Highlights

* 🔬 **Deep Learning Model**: EfficientNetB4 for lung cancer classification
* 🔁 **Online / Incremental Retraining**: Model retrains after accumulating new labeled samples
* 🧠 **Human-in-the-Loop Learning**: Predictions reviewed and fed back into training
* 📊 **MLflow Integration**: Tracks retrain & evaluation runs with metrics and parameters
* ⚙️ **Production-style Architecture**: FastAPI + Celery + Redis + PostgreSQL
* 🐳 **Dockerized Setup**: Fully containerized for reproducibility

---

## 🏗️ System Architecture

```
User Uploads Image
        ↓
FastAPI Backend
        ↓
EfficientNetB4 Inference
        ↓
Prediction Stored (Postgres)
        ↓
Human Review / Label Confirmation
        ↓
Retraining Trigger (Threshold-based)
        ↓
Celery Worker
        ↓
Model Retraining + Evaluation
        ↓
MLflow Tracking + Model Versioning
```

---

## 🧠 Model Details

* **Architecture**: EfficientNetB4
* **Input Size**: Configurable via environment variables
* **Classes**:

  * Adenocarcinoma
  * Benign
  * Squamous Carcinoma
* **Loss**: Categorical Crossentropy
* **Optimizer**: Adam

The backbone is partially frozen during retraining to support **incremental learning** without catastrophic forgetting.

---

## 🔁 Retraining Logic (Human-in-the-Loop)

* Model predictions are stored along with uploaded images
* Once a configurable threshold (`RETRAIN_THRESHOLD`) is reached:

  * Retraining is triggered automatically
  * New data is incorporated
  * A new model version is produced

Each retraining cycle produces:

* A **retrain run** (training metrics)
* A **nested evaluation run** (precision / recall / F1 per class)

---

## 📊 Experiment Tracking with MLflow

MLflow is used strictly for **experiment tracking and reproducibility**, not as a serving layer.

### What is tracked:

* 🔢 Metrics

  * Accuracy
  * Loss
  * Precision / Recall / F1 (per class)
* ⚙️ Parameters

  * Epochs
  * Batch size
  * Learning rate
  * Architecture
* 🧪 Run Types

  * `retrain_v1`, `retrain_v2`, ...
  * `eval_v1`, `eval_v2`, ... (nested runs)

This allows clear comparison between multiple retraining iterations.

---

## 🧩 Tech Stack

### Backend

* **FastAPI** – REST API
* **TensorFlow** – Deep Learning
* **Celery** – Background retraining tasks
* **Redis** – Task queue
* **PostgreSQL** – Prediction & metadata storage
* **MLflow** – Experiment tracking

### DevOps

* **Docker & Docker Compose**
* **Environment-based configuration**

---

## 🚀 Running the Project

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/lung-cancer-detection.git
cd lung-cancer-detection
```

### 2️⃣ Set environment variables

Create a `.env` file:

```env
POSTGRES_DB=lungdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
IMG_SIZE=224
EPOCHS=10
BATCH_SIZE=16
RETRAIN_THRESHOLD=50
```

### 3️⃣ Start services

```bash
docker compose up --build
```

* FastAPI → `http://localhost:8000`
* MLflow UI → `http://localhost:5001`

---

## 📈 What This Project Demonstrates

* Difference between **model training** and **ML systems**
* Importance of experiment tracking
* Handling retraining in production-style pipelines
* Practical limitations of tools like MLflow in containerized environments
* Clean separation of concerns (training vs serving vs tracking)

---

## 📜 License

This project is for educational and research purposes.
