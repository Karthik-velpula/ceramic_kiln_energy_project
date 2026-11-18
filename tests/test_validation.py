import pandas as pd
import pytest
from fastapi.testclient import TestClient
from kiln_energy.data import generate_dataset
from kiln_energy.features import engineer_features
from kiln_energy.api import app

def test_dataset_versions_have_minimum_rows_and_degraded_insulation():
    v1, v2 = generate_dataset(version=1), generate_dataset(version=2)
    assert len(v1) >= 250 and len(v2) >= 250
    assert v2.insulation_rating.mean() < v1.insulation_rating.mean()
    assert v2.energy_consumption_kwh.mean() > v1.energy_consumption_kwh.mean()

def test_feature_engineering_and_validation():
    row = generate_dataset(n=250).iloc[:1]
    features = engineer_features(row)
    assert "thermal_load_index" in features and "moisture_removal_load" in features
    invalid = row.copy(); invalid.loc[invalid.index[0], "insulation_rating"] = 1.5
    with pytest.raises(ValueError): engineer_features(invalid)

def test_api_rejects_out_of_range_input():
    client = TestClient(app)
    response = client.post("/predict", json={"pottery_load_kg": 20, "target_temperature_c": 1700,
      "initial_moisture_pct": 5, "planned_duration_hr": 8, "insulation_rating": .5,
      "kiln_volume_m3": 2, "ambient_temperature_c": 20})
    assert response.status_code == 422
