"""Train and evaluate a reproducible synthetic opportunity-screening model."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

FEATURES = ["demand", "traffic", "ev_adoption", "nearby_supply", "access", "population_density", "bev_growth"]
TARGET = "training_label"


def load_data(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = [field for field in FEATURES + [TARGET] if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Training CSV missing columns: " + ", ".join(missing))
        rows = list(reader)
    if len(rows) < 100:
        raise ValueError("At least 100 rows are required for a train/validation split")
    X = np.asarray([[float(row[key]) for key in FEATURES] for row in rows], dtype=np.float32)
    y = np.asarray([float(row[TARGET]) for row in rows], dtype=np.float32)
    if not np.isfinite(X).all() or not np.isfinite(y).all() or (X < 0).any() or (X > 100).any() or (y < 0).any() or (y > 100).any():
        raise ValueError("Features and target must be finite values between 0 and 100")
    return rows, X, y


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?", default=Path("data/candidates.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/model"))
    args = parser.parse_args()
    rows, X, y = load_data(args.input)
    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X, y, np.arange(len(y)), test_size=.2, random_state=42
    )
    model = ExtraTreesRegressor(n_estimators=100, max_depth=14, min_samples_leaf=5, max_features=.9, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    pred = np.clip(model.predict(X_test), 0, 100)
    metrics = {
        "rows": len(rows), "train_rows": len(train_idx), "test_rows": len(test_idx),
        "mae": round(float(mean_absolute_error(y_test, pred)), 3),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 3),
        "r2": round(float(r2_score(y_test, pred)), 4),
        "features": FEATURES, "target": TARGET,
        "target_notice": "Synthetic simulated screening label; not observed utilization or commercial performance.",
        "seed": 42, "trained_utc": datetime.now(timezone.utc).isoformat(),
        "feature_importance": {name: round(float(value), 4) for name, value in zip(FEATURES, model.feature_importances_)},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "target": TARGET, "metrics": metrics}, args.output_dir / "opportunity_model.joblib", compress=3)
    (args.output_dir / "training_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    prediction = np.clip(model.predict(X), 0, 100)
    scored_path = args.output_dir / "scored_candidates.csv"
    with scored_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) + ["model_score"])
        writer.writeheader()
        for row, value in zip(rows, prediction):
            writer.writerow({**row, "model_score": round(float(value), 2)})
    report = [
        "# Synthetic opportunity model · training report", "",
        f"Trained: {metrics['trained_utc']}", f"Rows: {metrics['rows']:,} ({metrics['train_rows']:,} train / {metrics['test_rows']:,} holdout)",
        "", "> **Important:** This model predicts an intentionally simulated label generated from synthetic assumptions. Holdout metrics only measure recovery of that synthetic label. They are not evidence of real-world demand, utilization, revenue, or investment performance.",
        "", "## Holdout metrics", "", f"- MAE: {metrics['mae']} points", f"- RMSE: {metrics['rmse']} points", f"- R²: {metrics['r2']}",
        "", "## Feature importance", "", *[f"- {key}: {value:.3f}" for key, value in sorted(metrics["feature_importance"].items(), key=lambda item: -item[1])],
        "", "## Reproducibility", "", "Estimator: ExtraTreesRegressor; 100 trees; maximum depth 14; minimum leaf size 5; 80/20 random split; seed 42. Features are screening indicators on a 0–100 scale.",
        "", "Validate on observed, licensed, geographically representative source data before making commercial or operational decisions.", ""
    ]
    (args.output_dir / "training_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Trained on {len(train_idx):,} rows; held out {len(test_idx):,}. MAE {metrics['mae']}, R² {metrics['r2']}")
    print(f"Model, metrics, report and {len(rows):,} scored rows saved under {args.output_dir}")


if __name__ == "__main__":
    main()
