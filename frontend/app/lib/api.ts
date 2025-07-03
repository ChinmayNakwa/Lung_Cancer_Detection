const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface PredictionResult {
  predicted_class: string;
  confidence: number;
  id: number;
  retraining_triggered?: boolean;
}

export interface Stats {
  unused_predictions: number;
  retrain_threshold: number;
  progress_percentage: number;
  active_model_version: number | null;
}

export interface ModelInfo {
  id: number;
  version: number;
  mlflow_run_id: string;
  is_active: boolean;
  created_at: string;
}

export async function uploadImage(file: File): Promise<PredictionResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error("Prediction failed");
  return res.json();
}

export async function correctPrediction(id: number, correctClass: string) {
  const res = await fetch(`${API_URL}/correct/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ corrected_class: correctClass }),
  });
  if (!res.ok) throw new Error("Correction failed");
  return res.json();
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_URL}/stats`, { cache: 'no-store' });
  return res.json();
}

export async function getModels(): Promise<{ models: ModelInfo[] }> {
  const res = await fetch(`${API_URL}/models`, { cache: 'no-store' });
  return res.json();
}

export async function triggerRetrain() {
  const res = await fetch(`${API_URL}/retrain`, { method: "POST" });
  return res.json();
}

export async function activateModel(version: number) {
  const res = await fetch(`${API_URL}/models/${version}/activate`, { method: "POST" });
  if (!res.ok) throw new Error("Activation failed");
  return res.json();
}