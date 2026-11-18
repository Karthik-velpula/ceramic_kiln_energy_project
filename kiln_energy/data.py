"""Deterministic synthetic kiln batch datasets, including an older kiln version."""
from pathlib import Path
import numpy as np
import pandas as pd

INPUT_COLUMNS = [
    "pottery_load_kg", "target_temperature_c", "initial_moisture_pct",
    "planned_duration_hr", "insulation_rating", "kiln_volume_m3",
    "ambient_temperature_c",
]
TARGET = "energy_consumption_kwh"

def generate_dataset(n: int = 600, seed: int = 42, version: int = 1) -> pd.DataFrame:
    if n < 250:
        raise ValueError("Each dataset version must contain at least 250 records")
    if version not in (1, 2):
        raise ValueError("version must be 1 or 2")
    rng = np.random.default_rng(seed + version)
    load = rng.uniform(20, 500, n)
    temp = rng.uniform(650, 1250, n)
    moisture = rng.uniform(1, 22, n)
    duration = rng.uniform(5, 24, n)
    volume = rng.uniform(0.8, 8, n)
    ambient = rng.uniform(5, 38, n)
    # Version 2 represents an aged kiln: lower insulation score and a higher heat-loss multiplier.
    insulation = rng.uniform(0.42, 0.78, n) if version == 1 else rng.uniform(0.20, 0.57, n)
    thermal = load * (temp - ambient) / 1000
    moisture_load = load * moisture / 100
    loss = duration * (1 - insulation) * (0.55 + volume / 12) * (temp - ambient) / 100
    energy = 5.2 + 0.72 * thermal + 0.31 * moisture_load + 1.8 * duration + loss
    if version == 2:
        energy *= 1.12
    energy += rng.normal(0, 3.0, n)
    frame = pd.DataFrame({
        "pottery_load_kg": load,
        "target_temperature_c": temp,
        "initial_moisture_pct": moisture,
        "planned_duration_hr": duration,
        "insulation_rating": insulation,
        "kiln_volume_m3": volume,
        "ambient_temperature_c": ambient,
        TARGET: np.maximum(energy, 0.1),
    })
    return frame.round(4)

def write_datasets(data_dir: str | Path = "data") -> tuple[Path, Path]:
    folder = Path(data_dir); folder.mkdir(parents=True, exist_ok=True)
    paths = (folder / "kiln_batches_v1.csv", folder / "kiln_batches_v2.csv")
    generate_dataset(version=1).to_csv(paths[0], index=False)
    generate_dataset(version=2).to_csv(paths[1], index=False)
    return paths
