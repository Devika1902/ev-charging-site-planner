# Synthetic opportunity model · training report

Trained: 2026-11-18T23:49:01.781086+00:00
Rows: 22,000 (17,600 train / 4,400 holdout)

> **Important:** This model predicts an intentionally simulated label generated from synthetic assumptions. Holdout metrics only measure recovery of that synthetic label. They are not evidence of real-world demand, utilization, revenue, or investment performance.

## Holdout metrics

- MAE: 3.281 points
- RMSE: 4.137 points
- R²: 0.8313

## Feature importance

- demand: 0.354
- ev_adoption: 0.228
- nearby_supply: 0.183
- traffic: 0.163
- bev_growth: 0.030
- access: 0.029
- population_density: 0.012

## Reproducibility

Estimator: ExtraTreesRegressor; 100 trees; maximum depth 14; minimum leaf size 5; 80/20 random split; seed 42. Features are screening indicators on a 0–100 scale.

Validate on observed, licensed, geographically representative source data before making commercial or operational decisions.
