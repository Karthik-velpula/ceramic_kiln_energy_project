"""FastAPI inference service. Load the trained artifact from artifacts/model.joblib."""
import os
from pathlib import Path
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .features import engineer_features

app = FastAPI(title="Ceramic Kiln Energy API", version="1.0.0")
# Allow the packaged HTML file to call the local-only API when opened directly.
# The regular app served from / remains same-origin and does not need CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

@app.get("/", include_in_schema=False)
def frontend():
    """Serve the single-page kiln energy application."""
    return FileResponse(WEB_DIR / "index.html")

class BatchInput(BaseModel):
    pottery_load_kg: float = Field(gt=0, le=10000)
    target_temperature_c: float = Field(ge=100, le=1600)
    initial_moisture_pct: float = Field(ge=0, le=100)
    planned_duration_hr: float = Field(gt=0, le=100)
    insulation_rating: float = Field(ge=0, le=1)
    kiln_volume_m3: float = Field(gt=0, le=1000)
    ambient_temperature_c: float = Field(ge=-50, le=70)

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": Path(os.getenv("KILN_MODEL_PATH", "artifacts/model.joblib")).exists()}

@app.post("/predict")
def predict(batch: BatchInput):
    model_path = Path(os.getenv("KILN_MODEL_PATH", "artifacts/model.joblib"))
    if not model_path.exists():
        raise HTTPException(status_code=503, detail="Model artifact not found; run python -m kiln_energy.pipeline first")
    try:
        model = joblib.load(model_path)
        payload = batch.model_dump() if hasattr(batch, "model_dump") else batch.dict()
        features = engineer_features(pd.DataFrame([payload]))
        estimate = max(0.0, float(model.predict(features)[0]))
        return {"predicted_energy_consumption_kwh": round(estimate, 3), "unit": "kWh"}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
