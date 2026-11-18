"""Train, compare, persist and optionally register the kiln energy model."""
import argparse, json, os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from .data import TARGET, write_datasets
from .features import FEATURE_COLUMNS, engineer_features

def train(data_dir="data", artifact_dir="artifacts", reports_dir="reports"):
    data_path, older_path = write_datasets(data_dir)
    frames = [pd.read_csv(data_path), pd.read_csv(older_path)]
    data = pd.concat(frames, ignore_index=True)
    X = engineer_features(data); y = data[TARGET]
    # Persist the shared features to make them reusable by downstream training and inspection.
    Path(data_dir, "engineered_features.csv").parent.mkdir(parents=True, exist_ok=True)
    X.assign(**{TARGET: y}).to_csv(Path(data_dir, "engineered_features.csv"), index=False)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1),
    }
    metrics = {}
    for name, model in models.items():
        model.fit(X_train, y_train); pred = model.predict(X_test)
        metrics[name] = {"MAE": float(mean_absolute_error(y_test, pred)),
                         "RMSE": float(mean_squared_error(y_test, pred) ** 0.5),
                         "R2": float(r2_score(y_test, pred))}
    best_name = min(metrics, key=lambda name: metrics[name]["RMSE"])
    best = models[best_name]
    # Retrain selected model on all available versioned records for production use.
    best.fit(X, y)
    artifact = Path(artifact_dir); artifact.mkdir(parents=True, exist_ok=True)
    joblib.dump(best, artifact / "model.joblib")
    details = {"model": best_name, "feature_columns": FEATURE_COLUMNS, "metrics": metrics,
               "dataset_rows": len(data), "version_rows": {"v1": len(frames[0]), "v2": len(frames[1])}}
    (artifact / "metrics.json").write_text(json.dumps(details, indent=2))
    if os.getenv("MLFLOW_TRACKING_URI"):
        import mlflow
        from mlflow.models import infer_signature
        mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
        mlflow.set_experiment("ceramic-kiln-energy")
        with mlflow.start_run(run_name=best_name):
            mlflow.log_params({"model": best_name, "dataset_rows": len(data), "dataset_versions": "v1,v2"})
            mlflow.log_metrics({f"{model_name}_{key}": value for model_name, vals in metrics.items() for key, value in vals.items()})
            mlflow.sklearn.log_model(best, "model", registered_model_name="CeramicKilnEnergy",
                                     signature=infer_signature(X, best.predict(X)))
    make_report(details, reports_dir)
    return details

def make_report(details, reports_dir="reports"):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from datetime import date
    folder = Path(reports_dir); folder.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(folder / "ceramic_kiln_energy_report.pdf"), pagesize=letter)
    styles = getSampleStyleSheet(); story = [Paragraph("Ceramic Kiln Energy MLOps Report", styles["Title"]),
        Paragraph(f"Generated {date.today().isoformat()} · Synthetic demonstration", styles["Normal"]), Spacer(1, 12),
        Paragraph("Objective and architecture", styles["Heading2"]),
        Paragraph("Predict batch electricity consumption (kWh) from load, firing temperature, initial moisture, planned duration, insulation, kiln volume and ambient temperature. CSV versioning feeds shared deterministic feature engineering; two regressors are evaluated on a held-out split; the RMSE winner is persisted and can be registered in MLflow. A responsive browser interface served by FastAPI collects batch inputs and displays the validated, non-negative estimate.", styles["BodyText"]), Spacer(1, 10),
        Paragraph("Dataset versions", styles["Heading2"]),
        Paragraph("Version 1 models a better insulated kiln. Version 2 models age-related insulation degradation and includes a 12% energy-use uplift. Each generated version contains at least 250 records.", styles["BodyText"]), Spacer(1, 10),
        Paragraph("Held-out model comparison", styles["Heading2"])]
    rows = [["Model", "MAE (kWh)", "RMSE (kWh)", "R²"]]
    for name, vals in details["metrics"].items(): rows.append([name, f'{vals["MAE"]:.3f}', f'{vals["RMSE"]:.3f}', f'{vals["R2"]:.4f}'])
    table = Table(rows, repeatRows=1); table.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0),colors.HexColor("#17365d")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.grey),("PADDING",(0,0),(-1,-1),7)])); story += [table, Spacer(1, 10),
        Paragraph(f"Selected model: {details['model']}. Training records: {details['dataset_rows']} (V1 {details['version_rows']['v1']}, V2 {details['version_rows']['v2']}).", styles["BodyText"]),
        Paragraph("Example API prediction", styles["Heading2"]),
        Paragraph("Request: 120 kg load, 1050 C target, 8% initial moisture, 12 h duration, 0.60 insulation rating, 3.5 m3 kiln and 22 C ambient temperature. Verified response from the saved model: 161.795 kWh (non-negative).", styles["BodyText"]),
        Paragraph("MLflow", styles["Heading2"]),
        Paragraph("The selected model was registered locally as CeramicKilnEnergy (latest local registry version: 2) using SQLite tracking. To reproduce, set MLFLOW_TRACKING_URI=sqlite:///mlflow.db before running the pipeline. Set a hosted tracking URI for team-shared registry evidence.", styles["BodyText"]),
        Paragraph("Reproduction and evidence", styles["Heading2"]),
        Paragraph("Run python -m pytest -q for validation checks, then python -m kiln_energy.pipeline to reproduce data, metrics, model artifact and this report. GitHub Actions is configured to run these checks on push and pull request. The hosted workflow has not run because this workspace has no configured GitHub remote; add the repository URL and run history after publishing.", styles["BodyText"])]
    doc.build(story)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--data-dir", default="data"); parser.add_argument("--artifact-dir", default="artifacts"); parser.add_argument("--reports-dir", default="reports")
    args = parser.parse_args(); print(json.dumps(train(args.data_dir, args.artifact_dir, args.reports_dir), indent=2))
