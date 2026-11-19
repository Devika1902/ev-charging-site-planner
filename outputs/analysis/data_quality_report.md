# Candidate screening · data quality report

Generated: 2026-11-18 23:46 UTC
Input: `data\candidates.csv`

> **Prototype warning:** Input data is user-provided. This pipeline does not fetch or certify official data. Demo records in this project are synthetic.

## Validation summary

- Input records: 22000
- Accepted records: 22000
- Rejected records: 0
- Confidence labels: {'Medium': 13424, 'High': 4408, 'Low': 4168}
- Score weights (normalized): demand 35%, traffic 25%, ev_adoption 25%, supply_gap 15%

## Findings

- No blocking validation errors.

## Interpretation limits

Scores are transparent screening indicators on a 0–100 scale, not forecasts of utilization, revenue or return. `nearby_supply` is treated as local supply coverage; supply gap is `100 - nearby_supply`. A high road-traffic score does not prove stopping demand. Coordinate precision and site feasibility must be independently verified.

Open Charge Map is useful for exploratory mapping but is not a complete authoritative station inventory; coverage, record quality, licensing and attribution can vary. Validate source terms and attribution for every use. Separate BEV from PHEV demand and check grid, access, land, permits and station uptime before decisions.
