# Allego Germany · EV Charging Network Planning

**Explore the live dashboard:** [EV Charging Network Planning](https://site-dist-theta-indol.vercel.app)

A decision-support prototype for screening where new high-power EV charging sites in Germany may be commercially attractive. It combines a 22,000-row synthetic planning dataset, an interactive browser dashboard, an explainable weighted ranking, and a Python machine-learning and analysis pipeline.

> **Important data notice:** The included locations, indicators, labels, and predictions are synthetic and are provided to demonstrate the workflow. They are not official market evidence, an investment recommendation, Allego plans, or evidence of land rights. The model predicts a simulated teaching label rather than observed commercial outcomes. The map uses approximate city-area markers and is not a parcel or boundary map.

## Business problem

Charging-network planners need to decide where to investigate new sites when investment and development capacity are limited. A candidate can look promising because it has high demand potential, traffic, and EV adoption, yet still be a poor choice if nearby charging coverage is already strong, the site is difficult to access, or the evidence is uncertain.

The practical question is: **which locations should be screened first for further commercial, grid, land, and permitting due diligence?** This prototype makes the screening criteria visible, lets users change their priorities, and produces a ranked shortlist for discussion. It supports early-stage prioritization; it does not make a final investment or site-selection decision.

## Solution

The dashboard lets a planner:

- Explore candidate locations in an overview and schematic opportunity map.
- Filter and search the candidate set, inspect site details, and compare ranked candidates.
- Rank candidates with either an adjustable weighted score or the trained model predictions.
- Change the relative importance of demand, traffic, EV adoption, and a local supply gap.
- Import a candidate CSV, export shortlist data, and print a management report.
- Review methodology, data limitations, and recommendations for validating real-world inputs.

The browser app is static and has no JavaScript build step. It reads the generated candidate and scored-candidate CSV files from the project. The pipeline creates the synthetic planning cells, trains the estimator, and produces tabular, GIS, quality, and spreadsheet outputs.

## Business-to-technical translation

### Decision unit

Each row represents a hypothetical candidate planning cell with a location and region, indicator values, access and confidence information, and coordinates. There are 22,000 generated rows in the included dataset.

### Screening score

The transparent baseline score is a normalized weighted sum:

```text
score = demand × w_demand
      + traffic × w_traffic
      + EV adoption × w_EV adoption
      + supply gap × w_supply gap

supply gap = 100 − nearby supply
```

All indicator values use a 0–100 scale. Weights are normalized to 100% in the UI; the defaults are 35% demand, 25% traffic, 25% EV adoption, and 15% supply gap. This turns the business priorities into a repeatable ranking that planners can inspect and adjust. Access and confidence are shown as supporting context rather than treated as proven commercial outcomes.

### Model and validation

`pipeline/train_model.py` fits an Extra Trees regressor on the generated data with a fixed 80/20 train/holdout split and seed 42. The generated suitability label is synthetic, so holdout metrics describe recovery of that label only. They do not establish real-world demand, profitability, or model performance. The UI keeps the transparent weighted score available as an alternative to the model ranking.

### Intended real-world data investigation

The prototype does not fetch external data. A production analysis would investigate sources such as KBA regional BEV/PHEV registrations, Open Charge Map, Eurostat GISCO population grids, OpenStreetMap roads, and German traffic counts. Validate coverage, timestamps, licensing, attribution, station power and status, and distinguish BEVs from PHEVs. Commercial diligence should also address observed stopping behavior, grid connection, land access, permitting, costs, and expected utilization.

## Run the dashboard

Requires Python 3 for the simple local web server; there are no frontend package installs or build commands.

```powershell
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000). Serve the project root so the dashboard can load `data/candidates.csv` and `outputs/model/scored_candidates.csv`. Google Fonts are optional; system fonts are used offline.

## Rebuild the data, model, and analysis

Requires Python 3.10+. From the project root:

```powershell
python -m pip install -r requirements.txt
python pipeline/generate_demo_data.py --rows 22000 --output data/candidates.csv
python pipeline/train_model.py data/candidates.csv --output-dir outputs/model
python pipeline/analyze.py data/candidates.csv --output-dir outputs/analysis
```

The analysis command accepts optional `--demand`, `--traffic`, `--ev-adoption`, and `--supply-gap` weight arguments; defaults are 35, 25, 25, and 15.

The pipeline produces:

- `outputs/model/opportunity_model.joblib` — fitted Extra Trees regressor.
- `outputs/model/scored_candidates.csv` — candidate rows with model predictions, read by the dashboard.
- `outputs/model/training_metrics.json` and `training_report.md` — holdout metrics and reproducibility notes.
- `outputs/analysis/candidate_ranking.csv` — ranked decision matrix.
- `outputs/analysis/candidate_locations.geojson` — point features for GIS tools.
- `outputs/analysis/data_quality_report.md` — data checks and limitations.
- `outputs/analysis/decision_matrix.xlsx` — formatted spreadsheet (requires `openpyxl`).

## Candidate CSV format

Use **Data & methodology** in the dashboard to download a template. Required headers:

```text
location, region, demand, traffic, ev_adoption, nearby_supply, access, confidence, lat, lon
```

Optional headers are `opportunity` and `validation_note`. Indicator values must be numeric from 0 to 100; coordinates must be decimal degrees; confidence accepts `High`, `Medium`, or `Low`. Uploading a CSV replaces the candidate set in the current browser session. Reloading restores the generated dataset and model scores.

## Repository layout

```text
index.html, styles.css, app.js   Static dashboard source
pipeline/                        Data generation, model training, and analysis
 data/                            Synthetic candidate dataset and sample template
outputs/model/                    Trained model, scores, and metrics
outputs/analysis/                 Rankings, GeoJSON, quality report, spreadsheet
site-dist/                        Static assets/data deployed to Vercel
```

## Limitations and responsible use

Treat the output as an early-stage screening aid. Before prioritizing real investment, replace synthetic indicators with validated, appropriately licensed data; test coverage and bias; verify candidate coordinates and parcel conditions; and assess grid capacity, land rights, permitting, construction and operating costs, local competition, utilization, and charging behavior. The ranking should be reviewed by domain experts and should not be used alone to approve or reject a site.
