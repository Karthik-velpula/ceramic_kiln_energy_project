"""Input validation and deterministic feature engineering shared by training and serving."""
import pandas as pd
from .data import INPUT_COLUMNS

FEATURE_COLUMNS = INPUT_COLUMNS + ["thermal_load_index", "moisture_removal_load"]
BOUNDS = {
    "pottery_load_kg": (0.1, 10000), "target_temperature_c": (100, 1600),
    "initial_moisture_pct": (0, 100), "planned_duration_hr": (0.1, 100),
    "insulation_rating": (0, 1), "kiln_volume_m3": (0.1, 1000),
    "ambient_temperature_c": (-50, 70),
}

def validate_inputs(frame: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(INPUT_COLUMNS) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    result = frame[INPUT_COLUMNS].copy()
    for col in INPUT_COLUMNS:
        result[col] = pd.to_numeric(result[col], errors="coerce")
        if result[col].isna().any():
            raise ValueError(f"{col} must contain finite numeric values")
        if not result[col].map(lambda value: __import__('math').isfinite(value)).all():
            raise ValueError(f"{col} must contain finite numeric values")
        low, high = BOUNDS[col]
        if not result[col].between(low, high).all():
            raise ValueError(f"{col} must be between {low} and {high}")
    return result

def engineer_features(frame: pd.DataFrame) -> pd.DataFrame:
    checked = validate_inputs(frame)
    result = checked.copy()
    result["thermal_load_index"] = result.pottery_load_kg * (
        result.target_temperature_c - result.ambient_temperature_c
    ) / 1000
    result["moisture_removal_load"] = result.pottery_load_kg * result.initial_moisture_pct / 100
    return result[FEATURE_COLUMNS]
