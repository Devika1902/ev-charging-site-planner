#!/usr/bin/env python3
"""Transparent screening pipeline for illustrative EV charging candidates.

Inputs are CSV candidate indicators on a 0-100 scale. The script validates the
input, calculates a weighted score, and writes ranked CSV, GeoJSON, Markdown
quality report and (when openpyxl is installed) an Excel decision matrix.
It does not fetch or claim to validate official source data.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ["location", "region", "demand", "traffic", "ev_adoption", "nearby_supply", "access", "confidence", "lat", "lon"]
SCORE_FIELDS = ["demand", "traffic", "ev_adoption", "nearby_supply", "access"]


def read_candidates(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = [field for field in FIELDS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(missing))
        rows = []
        for number, raw in enumerate(reader, start=2):
            row = dict(raw)
            row["_row"] = number
            for key in SCORE_FIELDS + ["lat", "lon"]:
                try:
                    row[key] = float(row[key])
                except (TypeError, ValueError):
                    row[key] = None
            rows.append(row)
    return rows


def validate(rows: list[dict]) -> tuple[list[dict], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    accepted: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        number = row["_row"]
        if not row.get("location") or not row.get("region"):
            errors.append(f"Row {number}: location and region are required")
            continue
        key = row["location"].strip().casefold()
        if key in seen:
            errors.append(f"Row {number}: duplicate location '{row['location']}'")
            continue
        seen.add(key)
        invalid = [field for field in SCORE_FIELDS if row[field] is None or not 0 <= row[field] <= 100]
        if invalid:
            errors.append(f"Row {number}: missing/out-of-range 0-100 value for {', '.join(invalid)}")
            continue
        if row["lat"] is None or row["lon"] is None or not -90 <= row["lat"] <= 90 or not -180 <= row["lon"] <= 180:
            errors.append(f"Row {number}: invalid decimal-degree coordinates")
            continue
        confidence = (row.get("confidence") or "").strip().title()
        if confidence not in {"Low", "Medium", "High"}:
            warnings.append(f"Row {number}: unrecognized confidence '{confidence}', set to Low")
            confidence = "Low"
        row["confidence"] = confidence
        accepted.append(row)
    if not accepted:
        errors.append("No valid candidate rows remain")
    return accepted, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Candidate CSV with the documented columns")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--demand", type=float, default=35)
    parser.add_argument("--traffic", type=float, default=25)
    parser.add_argument("--ev-adoption", type=float, default=25)
    parser.add_argument("--supply-gap", type=float, default=15)
    args = parser.parse_args()
    weight_map = {"demand": args.demand, "traffic": args.traffic, "ev_adoption": args.ev_adoption, "supply_gap": args.supply_gap}
    if any(not math.isfinite(v) or v < 0 for v in weight_map.values()) or sum(weight_map.values()) == 0:
        parser.error("Weights must be finite, non-negative, and sum to more than zero")
    try:
        raw_rows = read_candidates(args.input)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    rows, errors, warnings = validate(raw_rows)
    if not rows:
        parser.error("No valid rows; see validation findings: " + "; ".join(errors))
    total_weight = sum(weight_map.values())
    weights = {key: value / total_weight for key, value in weight_map.items()}
    for row in rows:
        row["supply_gap"] = 100 - row["nearby_supply"]
        row["opportunity_score"] = round(sum(row[key] * weights[key] for key in weight_map))
    rows.sort(key=lambda row: (-row["opportunity_score"], row["location"].casefold()))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    ranked_path = args.output_dir / "candidate_ranking.csv"
    public_fields = FIELDS + ["supply_gap", "opportunity_score", "opportunity", "validation_note"]
    with ranked_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=public_fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    geojson = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [row["lon"], row["lat"]]},
         "properties": {key: row.get(key) for key in ["location", "region", "opportunity_score", "demand", "traffic", "ev_adoption", "nearby_supply", "supply_gap", "access", "confidence"]}}
        for row in rows
    ]}
    (args.output_dir / "candidate_locations.geojson").write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")
    confidence_counts = Counter(row["confidence"] for row in rows)
    report = ["# Candidate screening · data quality report", "", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
              f"Input: `{args.input}`", "", "> **Prototype warning:** Input data is user-provided. This pipeline does not fetch or certify official data. Demo records in this project are synthetic.",
              "", "## Validation summary", "", f"- Input records: {len(raw_rows)}", f"- Accepted records: {len(rows)}", f"- Rejected records: {len(raw_rows) - len(rows)}",
              f"- Confidence labels: {dict(confidence_counts)}", f"- Score weights (normalized): {', '.join(f'{k} {v:.0%}' for k, v in weights.items())}",
              "", "## Findings", ""]
    report += [f"- ERROR: {item}" for item in errors] or ["- No blocking validation errors."]
    report += [f"- WARNING: {item}" for item in warnings]
    report += ["", "## Interpretation limits", "", "Scores are transparent screening indicators on a 0–100 scale, not forecasts of utilization, revenue or return. `nearby_supply` is treated as local supply coverage; supply gap is `100 - nearby_supply`. A high road-traffic score does not prove stopping demand. Coordinate precision and site feasibility must be independently verified.",
               "", "Open Charge Map is useful for exploratory mapping but is not a complete authoritative station inventory; coverage, record quality, licensing and attribution can vary. Validate source terms and attribution for every use. Separate BEV from PHEV demand and check grid, access, land, permits and station uptime before decisions.", ""]
    (args.output_dir / "data_quality_report.md").write_text("\n".join(report), encoding="utf-8")
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Decision matrix"
        columns = ["Rank"] + public_fields
        sheet.append(columns)
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="176B4A")
        for index, row in enumerate(rows, start=1):
            sheet.append([index] + [row.get(column, "") for column in public_fields])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            letter = column[0].column_letter
            sheet.column_dimensions[letter].width = min(max(max(len(str(cell.value or "")) for cell in column) + 2, 12), 44)
        workbook.save(args.output_dir / "decision_matrix.xlsx")
    except ImportError:
        warnings.append("openpyxl not installed: Excel workbook was not generated")
    print(f"Accepted {len(rows)}/{len(raw_rows)} candidates. Outputs: {args.output_dir.resolve()}")
    if errors:
        print("Validation issues:")
        for item in errors:
            print(" -", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
