"""Build the detailed, evidence-based Kilnwise project report PDF."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
GREEN = colors.HexColor("#284B3C")
DARK = colors.HexColor("#20251F")
CLAY = colors.HexColor("#BD684C")
MUTED = colors.HexColor("#687168")
PALE = colors.HexColor("#F1F4EF")
WARM = colors.HexColor("#F8F3ED")
GRID = colors.HexColor("#D9DED8")
REPOSITORY_URL = "https://github.com/Karthik-velpula/ceramic_kiln_energy_project"
CI_RUN_URL = REPOSITORY_URL + "/actions/runs/44278979628"


class SectionBand(Flowable):
    """Small colored band used to set off formulas and key takeaways."""
    def __init__(self, title: str, body: str, width: float):
        super().__init__()
        self.title, self.body, self.width = title, body, width
        self.body_para = Paragraph(body, ParagraphStyle(
            "BandBody", fontName="Helvetica", fontSize=8.2, leading=10,
            textColor=DARK,
        ))
        _, body_height = self.body_para.wrap(width - 30, 200)
        self.height = 15 + body_height + 10

    def draw(self):
        self.canv.setFillColor(PALE)
        self.canv.roundRect(0, 0, self.width, self.height, 7, fill=1, stroke=0)
        self.canv.setFillColor(GREEN)
        self.canv.roundRect(0, 0, 5, self.height, 2, fill=1, stroke=0)
        self.canv.setFillColor(GREEN)
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.drawString(15, self.height - 17, self.title)
        self.body_para.drawOn(self.canv, 15, 8)


def build_report(output_path: str | Path | None = None) -> Path:
    output_path = Path(output_path or ROOT / "reports" / "ceramic_kiln_energy_project_report.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path = ROOT / "artifacts" / "metrics.json"
    metrics = json.loads(metrics_path.read_text())
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="KTitle", parent=styles["Title"], fontName="Times-Bold",
        fontSize=29, leading=33, textColor=GREEN, alignment=TA_LEFT, spaceAfter=12))
    styles.add(ParagraphStyle(name="KSub", parent=styles["Normal"], fontSize=12, leading=18,
        textColor=MUTED, spaceAfter=10))
    styles.add(ParagraphStyle(name="KHead", parent=styles["Heading1"], fontName="Times-Bold",
        fontSize=22, leading=26, textColor=GREEN, spaceBefore=2, spaceAfter=12))
    styles.add(ParagraphStyle(name="KHead2", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=12, leading=15, textColor=GREEN, spaceBefore=9, spaceAfter=6))
    styles.add(ParagraphStyle(name="KBody", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9, leading=13, textColor=DARK, spaceAfter=7))
    styles.add(ParagraphStyle(name="KSmall", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.5, leading=10, textColor=DARK))
    styles.add(ParagraphStyle(name="KCellHead", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=7.5, leading=9, textColor=colors.white))
    styles.add(ParagraphStyle(name="KCallout", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=9.2, leading=13, textColor=GREEN))
    styles.add(ParagraphStyle(name="KCoverMeta", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=12, textColor=CLAY, spaceAfter=8))
    P = lambda text, style="KBody": Paragraph(text, styles[style])

    def table(rows, widths, header=True, font=7.5, padd=6):
        wrapped = []
        for ri, row in enumerate(rows):
            wrapped.append([P(str(cell), "KCellHead" if header and ri == 0 else "KSmall") for cell in row])
        t = Table(wrapped, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
        commands = [
            ("GRID", (0, 0), (-1, -1), 0.45, GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), padd),
            ("RIGHTPADDING", (0, 0), (-1, -1), padd),
            ("TOPPADDING", (0, 0), (-1, -1), padd),
            ("BOTTOMPADDING", (0, 0), (-1, -1), padd),
        ]
        if header:
            commands += [("BACKGROUND", (0, 0), (-1, 0), GREEN),
                         ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE])]
        else:
            commands += [("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, PALE])]
        t.setStyle(TableStyle(commands))
        return t

    def page_header(canvas, doc):
        canvas.saveState()
        w, h = letter
        if doc.page > 1:
            canvas.setStrokeColor(GRID); canvas.setLineWidth(.5)
            canvas.line(doc.leftMargin, h - 35, w - doc.rightMargin, h - 35)
            canvas.setFont("Helvetica-Bold", 7); canvas.setFillColor(GREEN)
            canvas.drawString(doc.leftMargin, h - 27, "KILNWISE  /  CERAMIC KILN ENERGY MLOPS")
        canvas.setStrokeColor(GRID); canvas.line(doc.leftMargin, 34, w - doc.rightMargin, 34)
        canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 7)
        canvas.drawString(doc.leftMargin, 22, "Synthetic demonstration project | Generated " + date.today().isoformat())
        canvas.drawRightString(w - doc.rightMargin, 22, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(output_path), pagesize=letter,
        rightMargin=.68*inch, leftMargin=.68*inch, topMargin=.66*inch,
        bottomMargin=.58*inch, title="Kilnwise Ceramic Kiln Energy MLOps Project Report",
        author="Kilnwise project")
    usable = letter[0] - doc.leftMargin - doc.rightMargin
    story = []

    # 1. Cover and executive summary.
    story += [Spacer(1, .5*inch), P("PROJECT REPORT  /  MLOPS APPLICATION", "KCoverMeta"),
        P("Ceramic Kiln<br/>Energy Estimator", "KTitle"),
        P("A detailed guide to Kilnwise: synthetic data, feature engineering, model selection, MLflow, API serving, browser interface, automation, and reproducibility.", "KSub"),
        Spacer(1, 10),
        SectionBand("PROJECT GOAL", "Estimate electricity consumption in kWh for a scheduled ceramic firing batch.", usable),
        Spacer(1, 18), P("Executive summary", "KHead2"),
        P("Kilnwise is an end-to-end demonstration of a small machine-learning application. A user enters seven kiln and batch conditions in a browser form. FastAPI validates the request, applies the same feature transformations used during training, and returns an estimate from a saved regression model. The project generates two versioned synthetic datasets, compares Linear Regression with Random Forest Regression, stores artifacts and metrics, supports MLflow registration, and defines a GitHub Actions workflow.")]
    rows = [["Selected model", "Records", "MAE", "RMSE", "R2"],
            [metrics["model"], str(metrics["dataset_rows"]),
             f'{metrics["metrics"][metrics["model"]]["MAE"]:.2f} kWh',
             f'{metrics["metrics"][metrics["model"]]["RMSE"]:.2f} kWh',
             f'{metrics["metrics"][metrics["model"]]["R2"]:.4f}']]
    story += [table(rows, [1.45*inch, .8*inch, 1.0*inch, 1.05*inch, .65*inch]), Spacer(1, 14),
        P("How to read this report", "KHead2"),
        P("The reported performance is measured on held-out records drawn from synthetic data. It explains how the pipeline works; it is not evidence of calibrated energy forecasts for a real kiln. The project has been pushed to <link href='" + REPOSITORY_URL + "' color='#284B3C'>GitHub</link>, and the push-triggered CI run passed.") , PageBreak()]

    # 2. Product and architecture.
    story += [P("1. Project overview", "KHead"),
        P("The application answers one operational question: approximately how many kilowatt-hours should a planned firing batch consume? The estimate can support early planning and comparisons between batch conditions. It is a supervised regression problem because the target is a continuous numeric value.") ,
        P("Application flow", "KHead2")]
    flow = [["1. Batch form", "2. FastAPI", "3. Feature logic", "4. Saved model", "5. kWh result"],
            ["User enters kiln and firing conditions", "Checks fields and ranges", "Derives thermal and moisture loads", "Predicts from nine features", "Returns a non-negative estimate"]]
    story += [table(flow, [1.35*inch]*5), Spacer(1, 10),
        P("System components", "KHead2"),
        table([["Component", "Purpose", "Project location"],
               ["Data generator", "Builds reproducible synthetic V1 and V2 rows.", "kiln_energy/data.py"],
               ["Feature layer", "Validates fields and derives model inputs.", "kiln_energy/features.py"],
               ["Training pipeline", "Splits, fits, scores, selects, persists and optionally registers.", "kiln_energy/pipeline.py"],
               ["Inference service", "Serves the web page, health check, and prediction endpoint.", "kiln_energy/api.py"],
               ["Browser UI", "Collects batch inputs and presents estimate and service status.", "web/index.html"],
               ["CI workflow", "Runs tests, retrains and checks non-negative predictions.", ".github/workflows/ci.yml"]],
              [1.25*inch, 3.15*inch, 1.7*inch]), Spacer(1, 7),
        P("The web UI and API are served from the same FastAPI application when opened at http://127.0.0.1:8000. The /docs path exposes interactive API documentation; /health reports service and model-file availability."), PageBreak()]

    # 3. Dataset.
    story += [P("2. Dataset creation and versioning", "KHead"),
        P("The project creates 600 synthetic records in each of two CSV versions. A fixed NumPy random generator seed makes the generated values reproducible. Version 1 represents a comparatively well-insulated kiln. Version 2 represents an older kiln with a lower insulation range and an energy uplift."),
        P("Generated operating ranges", "KHead2"),
        table([["Variable", "Synthetic range", "Unit"],
               ["Pottery load", "20 to 500", "kg"],
               ["Target firing temperature", "650 to 1,250", "C"],
               ["Initial moisture", "1 to 22", "%"],
               ["Planned duration", "5 to 24", "hours"],
               ["Kiln insulation V1", "0.42 to 0.78", "relative score"],
               ["Kiln insulation V2", "0.20 to 0.57", "relative score"],
               ["Kiln volume", "0.8 to 8", "m3"],
               ["Ambient temperature", "5 to 38", "C"]],
              [2.15*inch, 2.1*inch, 1.25*inch]), Spacer(1, 9),
        P("Synthetic target construction", "KHead2"),
        P("The generator first calculates thermal and moisture loads, then creates a base energy target using those terms, duration, and an insulation-dependent heat-loss term. Version 2 applies a 12% uplift before Gaussian noise is added. Negative values are clipped to 0.1 kWh. This formula creates a learnable relationship; it is synthetic ground truth, not a measured kiln law."),
        SectionBand("SIMULATION FORMULA", "energy = 5.2 + 0.72 x thermal_load + 0.31 x moisture_load + 1.8 x duration + heat_loss; V2: base energy x 1.12; then noise (std 3 kWh).", usable),
        Spacer(1, 8),
        P("The heat-loss term is duration x (1 - insulation) x (0.55 + kiln_volume/12) x (target_temperature - ambient_temperature) / 100. The final generated target is rounded to four decimal places. Dataset files are data/kiln_batches_v1.csv and data/kiln_batches_v2.csv; the combined transformed matrix is data/engineered_features.csv."), PageBreak()]

    # 4. Inputs, validation and engineering.
    story += [P("3. Inputs, validation, and feature engineering", "KHead"),
        P("The frontend groups values by firing batch and kiln environment. The API applies the same limits on every request so training and serving use a consistent feature contract."),
        table([["Input", "Meaning", "Accepted API range"],
               ["pottery_load_kg", "Total ceramic batch weight.", "0.1 to 10,000 kg"],
               ["target_temperature_c", "Planned peak firing temperature.", "100 to 1,600 C"],
               ["initial_moisture_pct", "Starting material moisture percentage.", "0 to 100%"],
               ["planned_duration_hr", "Planned firing-cycle duration.", "0.1 to 100 h"],
               ["insulation_rating", "Relative insulation efficiency; higher means better.", "0 to 1"],
               ["kiln_volume_m3", "Internal kiln volume.", "0.1 to 1,000 m3"],
               ["ambient_temperature_c", "Temperature surrounding the kiln.", "-50 to 70 C"]],
              [1.85*inch, 2.8*inch, 1.55*inch]), Spacer(1, 9),
        P("Two derived features", "KHead2"),
        table([["Feature", "Definition", "Purpose"],
               ["thermal_load_index", "load_kg x (target_C - ambient_C) / 1,000", "Combines batch mass and temperature lift."],
               ["moisture_removal_load", "load_kg x initial_moisture_pct / 100", "Approximates moisture mass associated with the batch."]],
              [1.45*inch, 2.6*inch, 2.15*inch]), Spacer(1, 9),
        P("Worked feature example", "KHead2"),
        P("For 120 kg of pottery, target 1,050 C, ambient 22 C and initial moisture 8%: thermal_load_index = 120 x (1,050 - 22) / 1,000 = 123.36; moisture_removal_load = 120 x 8 / 100 = 9.6. The model receives the seven original inputs plus these two engineered values, for nine input features total."),
        P("Validation rejects missing, non-numeric, infinite, or out-of-range values. Pydantic returns a 422 response for invalid requests. The prediction output is clipped to at least zero and rounded to three decimal places."), PageBreak()]

    # 5. Training pipeline and models.
    story += [P("4. Training pipeline and model choices", "KHead"),
        P("The pipeline regenerates both dataset versions, concatenates their 1,200 rows, engineers features, and persists the feature snapshot. It then creates a random 80/20 train/test split with random_state=42. The test set is used to compare model performance; after selection, the winning estimator is fitted again on all 1,200 records for the saved serving artifact."),
        P("Models implemented", "KHead2"),
        table([["Estimator", "Configuration", "Role"],
               ["Linear Regression", "scikit-learn LinearRegression defaults.", "Fits a linear combination of the nine input features."],
               ["Random Forest Regression", "250 trees; min_samples_leaf=2; random_state=42; n_jobs=-1.", "Averaging ensemble of decision trees, able to represent non-linear splits."],
               ["Selection rule", "Minimum held-out RMSE.", "Chooses one candidate for final retraining and API serving."]],
              [1.55*inch, 2.2*inch, 2.45*inch]), Spacer(1, 9),
        P("Pipeline sequence", "KHead2"),
        table([["Stage", "What happens", "Output"],
               ["1. Generate", "Create V1 and V2 with the configured seed.", "Two versioned CSVs"],
               ["2. Transform", "Validate and derive the two load features.", "Reusable feature CSV"],
               ["3. Split", "80% train, 20% test; fixed split seed.", "Train and test matrices"],
               ["4. Fit and score", "Fit both regressors; compute MAE, RMSE, R2.", "Comparable metrics"],
               ["5. Select and refit", "Choose lowest RMSE; fit winner on all rows.", "artifacts/model.joblib"],
               ["6. Record", "Write metrics; optionally log model and metrics to MLflow.", "metrics.json and MLflow run"]],
              [1.2*inch, 3.35*inch, 1.65*inch]), Spacer(1, 7),
        P("The split is performed after concatenating versions, so both simulated kiln versions can appear in training and test data. This evaluates random held-out batches from the same synthetic generation process, not generalization to a completely unseen kiln."), PageBreak()]

    # 6. Model results.
    story += [P("5. Evaluation results and interpretation", "KHead"),
        P("All scores below use the same held-out 20% partition. Lower MAE and RMSE are better; an R2 nearer 1 indicates a stronger fit to the held-out target variation."),
        table([["Model", "MAE (kWh)", "RMSE (kWh)", "R2", "Decision"],
               ["Linear Regression", "15.009", "18.784", "0.9776", "Selected"],
               ["Random Forest Regression", "17.383", "22.914", "0.9667", "Not selected"]],
              [1.75*inch, 1.05*inch, 1.05*inch, .7*inch, 1.2*inch]), Spacer(1, 9),
        P("Metric definitions", "KHead2"),
        table([["Metric", "Plain-language meaning", "Current Linear Regression score"],
               ["MAE", "Average absolute prediction error; easier to interpret in kWh.", "About 15.01 kWh"],
               ["RMSE", "Square root of average squared error; larger errors count more.", "About 18.78 kWh"],
               ["R2", "Fraction of held-out target variation explained relative to a mean baseline.", "About 0.9776"]],
              [0.72*inch, 3.7*inch, 1.58*inch]), Spacer(1, 9),
        SectionBand("MODEL CHOICE", "Linear Regression wins on this fixed synthetic holdout: RMSE is about 4.13 kWh lower than Random Forest.", usable),
        Spacer(1, 8),
        P("The saved Linear Regression intercept is approximately 16.9200. The nine fitted coefficients are stored inside artifacts/model.joblib; they are learned jointly and should not be interpreted as isolated causal effects because several features are correlated or derived from other inputs."),
        P("These scores are unusually strong in part because generated energy follows a relatively structured formula. Random noise, the fixed random split, and shared synthetic generation assumptions influence the result. Validate with real meter readings and a kiln-based holdout before operational use."), PageBreak()]

    # 7. Prediction service and frontend.
    story += [P("6. Prediction API and browser application", "KHead"),
        P("FastAPI exposes the inference service and serves the responsive Kilnwise browser interface at the root path. In normal use, the HTML and API share an origin, avoiding a separate frontend build or frontend server."),
        table([["Route", "Method", "Purpose"],
               ["/", "GET", "Serves the Kilnwise form and result screen."],
               ["/health", "GET", "Returns service status and whether the model file exists."],
               ["/predict", "POST", "Validates a batch, engineers features and returns predicted kWh."],
               ["/docs", "GET", "Interactive Swagger API documentation."]],
              [1.0*inch, .75*inch, 4.25*inch]), Spacer(1, 8),
        P("Example request", "KHead2"),
        P('{"pottery_load_kg":120, "target_temperature_c":1050, "initial_moisture_pct":8, "planned_duration_hr":12, "insulation_rating":0.6, "kiln_volume_m3":3.5, "ambient_temperature_c":22}', "KSmall"),
        P("Example response from the saved model: predicted_energy_consumption_kwh = 161.795, unit = kWh. The frontend shows a service-status indicator, groups fields into batch/firing and kiln/environment sections, reports input errors, disables the submit action while calculating, and displays the result in a dedicated estimate panel."),
        P("The API loads artifacts/model.joblib and applies the shared engineer_features function, so validation and feature definitions are reused rather than reimplemented in the browser. The frontend sends only the seven raw fields; it does not compute a hand-written final energy formula."),
        P("Starting the application", "KHead2"),
        P("macOS: double-click run_app.command. Manual start: activate .venv, then run uvicorn kiln_energy.api:app --reload. Open http://127.0.0.1:8000. If index.html is opened directly as a file, it is configured to call the local API at port 8000; the API permits the opaque file origin for this local development workflow."), PageBreak()]

    # 7. Application outputs supplied by the user.
    screenshot_one = ROOT / "reports" / "images" / "kilnwise_output_01.png"
    screenshot_two = ROOT / "reports" / "images" / "kilnwise_output_02.png"
    if screenshot_one.exists() and screenshot_two.exists():
        story += [P("7. Application output evidence", "KHead"),
            P("The following screenshots show the Kilnwise browser application after estimates were returned. The screenshots are included as supplied project evidence; the values shown are outputs from the saved Linear Regression model."),
            P("Output 1 - 155 kg batch", "KHead2"),
            P("Inputs shown: 155 kg pottery, 1,050 C target, 8% moisture, 12-hour firing, 0.6 insulation rating, 3.5 m3 kiln and 22 C ambient temperature. Displayed estimate: 189.96 kWh."), Spacer(1, 4),
            Image(str(screenshot_one), width=usable, height=usable * 1658 / 2932),
            P("Figure 1. Kilnwise estimate for the 155 kg firing batch.", "KSmall"), PageBreak(),
            P("Application output evidence - continued", "KHead"),
            P("Inputs shown: 120 kg pottery, 1,400 C target, 8% moisture, 10-hour firing, 0.6 insulation rating, 3.7 m3 kiln and 20 C ambient temperature. Displayed estimate: 207.97 kWh."), Spacer(1, 4),
            Image(str(screenshot_two), width=usable, height=usable * 1646 / 2914),
            P("Figure 2. Kilnwise estimate for the 120 kg firing batch.", "KSmall"), PageBreak()]

    # 8. MLflow / CI.
    story += [P("8. MLflow, CI, and model delivery", "KHead"),
        P("MLflow integration is optional and enabled by MLFLOW_TRACKING_URI. When configured, the pipeline sets the ceramic-kiln-energy experiment, logs model and dataset parameters, records all six candidate metric values, logs the winning scikit-learn model with a signature, and registers it under CeramicKilnEnergy."),
        P("Recorded local registry evidence", "KHead2"),
        table([["Item", "Recorded state"],
               ["Tracking backend", "Local SQLite URI: sqlite:///mlflow.db"],
               ["Experiment", "ceramic-kiln-energy"],
               ["Registered model", "CeramicKilnEnergy"],
               ["Latest local registry version", "2 at the time of report preparation"],
               ["Hosted MLflow", "Not configured; local evidence is not a shared hosted registry"]],
              [2.0*inch, 4.0*inch]), Spacer(1, 9),
        P("Continuous integration", "KHead2"),
        P("The GitHub Actions workflow checks out the repository, installs the requirements on Python 3.11, runs the pytest validation suite, trains the pipeline, and checks that sample model outputs are non-negative. It is configured for pushes and pull requests. The published repository is <link href='" + REPOSITORY_URL + "' color='#284B3C'>Karthik-velpula/ceramic_kiln_energy_project</link>. Push-triggered workflow run <link href='" + CI_RUN_URL + "' color='#284B3C'>44278979628</link> completed successfully: dependency install, tests, training, and the non-negative output check all passed."),
        P("Local reproducibility evidence", "KHead2"),
        P("A three-test validation suite, training pipeline, and non-negative prediction check all passed in GitHub Actions run 44278979628. The metric artifact and registered model were also generated locally; the SQLite MLflow registry remains local, with no hosted MLflow tracking server or remote artifact store configured."),
        SectionBand("CI RESULT", "GitHub Actions run 44278979628 passed on main. The hosted workflow evidence is available at the linked run.", usable), PageBreak()]

    # 9. Reproducibility, file map, and operations.
    story += [P("9. Reproduce, run, and inspect the project", "KHead"),
        P("Requirements", "KHead2"),
        P("Python 3.10 or later and the packages listed in requirements.txt are used. An exact environment snapshot is available in requirements-lock.txt. The checked-in .venv is local environment state and should not be submitted as source."),
        P("Setup and run", "KHead2"),
        P("1) Create/activate the environment: python3 -m venv .venv && source .venv/bin/activate<br/>2) Install: pip install -r requirements.txt<br/>3) Train and rebuild outputs: python -m kiln_energy.pipeline<br/>4) Start UI/API: uvicorn kiln_energy.api:app --reload<br/>5) Open http://127.0.0.1:8000; API docs are at /docs.<br/>6) Run validations: python -m pytest -q"),
        P("Rebuild with MLflow local registry", "KHead2"),
        P("Set MLFLOW_TRACKING_URI=sqlite:///mlflow.db before running python -m kiln_energy.pipeline. This writes the local database and registers another version under CeramicKilnEnergy. For a shared registry, configure a hosted tracking URI and a supported registry backend."),
        P("Important files and generated outputs", "KHead2"),
        table([["Path", "Contents"],
               ["kiln_energy/data.py", "Versioned synthetic dataset generation."],
               ["kiln_energy/features.py", "Feature definitions, bounds, validation."],
               ["kiln_energy/pipeline.py", "Train/evaluate/save/register/report pipeline."],
               ["kiln_energy/api.py", "FastAPI UI and inference routes."],
               ["web/index.html", "Browser interface, validation, API request logic."],
               ["data/*.csv", "V1, V2 and engineered feature datasets."],
               ["artifacts/model.joblib", "Saved selected estimator used for inference."],
               ["artifacts/metrics.json", "Model metrics, selected model, feature list, row counts."],
               ["reports/", "Brief report and detailed project report PDFs."],
               [".github/workflows/ci.yml", "Automated test/train/output checks." ]],
              [2.35*inch, 3.65*inch]), PageBreak()]

    # 10. Limitations, next steps, glossary.
    story += [P("10. Limitations, recommendations, and glossary", "KHead"),
        P("Known limitations", "KHead2"),
        table([["Limitation", "Why it matters"],
               ["Synthetic labels", "The target is generated from an assumed formula and is not actual kiln meter data."],
               ["Random record split", "The same simulated V1/V2 generation process appears in train and test; this is not a new-kiln test."],
               ["No uncertainty interval", "The API returns one point estimate and does not quantify prediction uncertainty."],
               ["No drift monitoring", "The app does not track real prediction errors, usage, or shifts in kiln behavior."],
               ["Artifact locations", "Code, datasets, model, and reports are pushed to GitHub; the SQLite MLflow tracking database remains local."],
               ["Simplified input", "Insulation is a synthetic 0-to-1 score, not a standardized engineering measurement."]],
              [1.65*inch, 4.35*inch]), Spacer(1, 8),
        P("Recommended next steps for a real deployment", "KHead2"),
        P("Collect verified batch records and meter readings; document measurement units and sensor quality; split evaluation by kiln and time; compare against a simple baseline; tune models using cross-validation; quantify uncertainty; monitor prediction errors and input drift; use a hosted MLflow registry with access controls; pin and review dependencies; and publish to a GitHub repository so CI execution can be linked in the submission."),
        P("Glossary", "KHead2"),
        table([["Term", "Meaning"],
               ["kWh", "Kilowatt-hour, a unit of electrical energy."],
               ["MAE", "Mean Absolute Error; average magnitude of prediction error."],
               ["RMSE", "Root Mean Squared Error; penalizes larger errors more strongly."],
               ["R2", "Coefficient of determination; compares fit with a mean-target baseline."],
               ["Feature", "A numeric input used by a machine-learning model."],
               ["Model registry", "A catalog of named, versioned model artifacts in MLflow."],
               ["CI", "Continuous Integration; automated checks run on repository changes."]],
              [1.25*inch, 4.75*inch]), Spacer(1, 10),
        SectionBand("CONCLUSION", "Kilnwise demonstrates the full path from versioned data to a browser-based prediction. Real operational decisions require validation against measured kiln data.", usable)]

    doc.build(story, onFirstPage=page_header, onLaterPages=page_header)
    return output_path


if __name__ == "__main__":
    print(build_report())
