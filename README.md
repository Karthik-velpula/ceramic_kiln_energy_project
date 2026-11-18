# Ceramic Kiln Energy MLOps

End-to-end example for estimating electricity use (kWh) for a scheduled ceramic firing batch.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m kiln_energy.pipeline --data-dir data --artifact-dir artifacts
uvicorn kiln_energy.api:app --reload
```

Open `http://127.0.0.1:8000` for the Kilnwise frontend. Use `/docs` for the API explorer. On macOS, double-click `run_app.command` to start the app and open it in your browser. The pipeline generates both dataset versions, persists engineered features, fits and compares Linear Regression and Random Forest, saves the selected model and metrics, and (when enabled) logs/registers it with MLflow. To use MLflow locally, set `MLFLOW_TRACKING_URI=sqlite:///mlflow.db` when running the pipeline.

Generate the detailed, multi-page project report from the current metrics and artifacts with `python -m kiln_energy.detailed_report`. The output is `reports/ceramic_kiln_energy_project_report.pdf`.

If package installation is unavailable, run `python -m kiln_energy.generate_data_stdlib` to generate both versioned CSVs using only the Python standard library. Training and PDF generation require the packages in `requirements.txt`.

## Inputs and features

Required batch fields: `pottery_load_kg`, `target_temperature_c`, `initial_moisture_pct`, `planned_duration_hr`, `insulation_rating`, `kiln_volume_m3`, and `ambient_temperature_c`. The pipeline derives `thermal_load_index` and `moisture_removal_load`. Input validation enforces physical bounds; predictions are floored at zero.

## Reproducibility and evidence

Run `python -m kiln_energy.pipeline` to regenerate CSVs, metrics, plots, model artifacts, and `reports/ceramic_kiln_energy_report.pdf`. The GitHub Actions workflow runs validation and non-negative prediction checks after the project is pushed. Check the repository's Actions tab for hosted run history.

## Layout

- `kiln_energy/`: data generation, feature store, training, API, report.
- `web/index.html`: responsive browser application served by FastAPI.
- `run_app.command`: one-click macOS launcher.
- `data/`: generated dataset versions and reusable feature snapshots.
- `artifacts/`: selected model, model metadata, and metrics.
- `reports/`: generated PDF report and figures.
- `reports/images/`: supplied Kilnwise output screenshots embedded in the detailed report.
- `kiln_energy/detailed_report.py`: generator for the multi-page project report.
- `.github/workflows/ci.yml`: automated checks.
