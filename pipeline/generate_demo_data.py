"""Create a reproducible 22,000-row synthetic Germany screening dataset.

The generated rows are artificial planning-grid examples. The target is a
simulated label for demonstrating model training, never observed utilization.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

PLACES = [
    ("Schleswig-Holstein", "Kiel", 54.323, 10.123, .50, .46, .44, .48, .54),
    ("Schleswig-Holstein", "Lübeck", 53.865, 10.687, .49, .51, .43, .49, .60),
    ("Hamburg", "Hamburg", 53.551, 9.993, .83, .82, .78, .62, .88),
    ("Lower Saxony", "Hanover", 52.376, 9.732, .69, .75, .64, .57, .83),
    ("Lower Saxony", "Braunschweig", 52.269, 10.526, .60, .66, .60, .54, .72),
    ("Lower Saxony", "Osnabrück", 52.280, 8.047, .55, .60, .52, .48, .71),
    ("Bremen", "Bremen", 53.079, 8.801, .64, .74, .61, .50, .78),
    ("Mecklenburg-Western Pomerania", "Rostock", 54.092, 12.099, .43, .54, .48, .40, .64),
    ("Mecklenburg-Western Pomerania", "Schwerin", 53.635, 11.401, .40, .47, .43, .38, .59),
    ("Brandenburg", "Potsdam", 52.391, 13.064, .64, .59, .69, .49, .71),
    ("Brandenburg", "Cottbus", 51.757, 14.328, .42, .47, .44, .37, .63),
    ("Berlin", "Berlin", 52.520, 13.405, .90, .78, .88, .69, .82),
    ("Saxony-Anhalt", "Magdeburg", 52.120, 11.627, .50, .61, .50, .40, .76),
    ("Saxony-Anhalt", "Halle", 51.482, 11.970, .53, .61, .54, .42, .75),
    ("Saxony", "Leipzig", 51.340, 12.375, .68, .67, .67, .45, .77),
    ("Saxony", "Dresden", 51.050, 13.738, .68, .66, .65, .51, .75),
    ("Thuringia", "Erfurt", 50.984, 11.029, .53, .58, .52, .40, .74),
    ("Thuringia", "Jena", 50.928, 11.589, .56, .51, .57, .43, .67),
    ("North Rhine-Westphalia", "Cologne", 50.938, 6.960, .84, .85, .78, .75, .82),
    ("North Rhine-Westphalia", "Düsseldorf", 51.228, 6.773, .83, .84, .81, .77, .86),
    ("North Rhine-Westphalia", "Dortmund", 51.514, 7.466, .72, .79, .67, .58, .83),
    ("North Rhine-Westphalia", "Münster", 51.961, 7.626, .68, .62, .74, .53, .70),
    ("North Rhine-Westphalia", "Bonn", 50.737, 7.098, .70, .69, .74, .55, .72),
    ("Hesse", "Frankfurt", 50.111, 8.682, .84, .88, .80, .74, .91),
    ("Hesse", "Kassel", 51.313, 9.479, .54, .69, .52, .42, .87),
    ("Hesse", "Darmstadt", 49.872, 8.651, .71, .66, .76, .58, .71),
    ("Rhineland-Palatinate", "Mainz", 50.000, 8.271, .68, .70, .68, .55, .79),
    ("Rhineland-Palatinate", "Koblenz", 50.356, 7.589, .56, .64, .56, .43, .77),
    ("Saarland", "Saarbrücken", 49.240, 6.996, .58, .62, .58, .46, .73),
    ("Baden-Württemberg", "Stuttgart", 48.776, 9.183, .87, .80, .87, .78, .77),
    ("Baden-Württemberg", "Mannheim", 49.488, 8.467, .75, .82, .74, .64, .88),
    ("Baden-Württemberg", "Freiburg", 47.999, 7.842, .75, .59, .82, .63, .66),
    ("Baden-Württemberg", "Karlsruhe", 49.006, 8.404, .73, .75, .74, .60, .83),
    ("Bavaria", "Munich", 48.137, 11.576, .89, .82, .88, .78, .80),
    ("Bavaria", "Nuremberg", 49.453, 11.077, .72, .79, .70, .62, .88),
    ("Bavaria", "Augsburg", 48.371, 10.898, .69, .67, .72, .51, .73),
    ("Bavaria", "Regensburg", 49.013, 12.102, .64, .68, .67, .50, .79),
    ("Bavaria", "Würzburg", 49.791, 9.953, .61, .69, .62, .47, .83),
]

HEADERS = ["candidate_id", "location", "region", "demand", "traffic", "ev_adoption", "nearby_supply", "access", "population_density", "bev_growth", "confidence", "lat", "lon", "training_label", "opportunity", "validation_note"]


def create_rows(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for idx in range(count):
        region, city, lat0, lon0, pop0, traffic0, ev0, supply0, access0 = PLACES[idx % len(PLACES)]
        # Cluster points around real city centers; offsets represent fictional
        # 1 km planning cells, not parcel coordinates or confirmed sites.
        lat = lat0 + rng.gauss(0, .035)
        lon = lon0 + rng.gauss(0, .052)
        population = max(0, min(100, round((pop0 + rng.gauss(0, .16)) * 100, 1)))
        traffic = max(0, min(100, round((traffic0 + rng.gauss(0, .17)) * 100, 1)))
        ev = max(0, min(100, round((ev0 + rng.gauss(0, .15)) * 100, 1)))
        supply = max(0, min(100, round((supply0 + rng.gauss(0, .17)) * 100, 1)))
        access = max(0, min(100, round((access0 + rng.gauss(0, .12)) * 100, 1)))
        bev_growth = max(0, min(100, round((.30 + .54 * (ev / 100) + rng.gauss(0, .12)) * 100, 1)))
        demand = max(0, min(100, round(.34 * ev + .34 * population + .18 * bev_growth + .14 * access + rng.gauss(0, 5), 1)))
        gap = 100 - supply
        # Synthetic suitability label: a nonlinear teaching target, not an
        # observed commercial outcome. It is reproducible and noise-injected.
        label = (.29 * demand + .19 * traffic + .19 * ev + .23 * gap + .10 * access
                 + .0015 * max(0, demand - 60) * max(0, gap - 45)
                 - .0010 * max(0, supply - 70) * traffic + rng.gauss(0, 4.0))
        label = round(max(0, min(100, label)), 2)
        confidence = "High" if rng.random() < .20 else ("Medium" if rng.random() < .76 else "Low")
        number = idx + 1
        rows.append({
            "candidate_id": f"DE-SYN-{number:05d}",
            "location": f"{city} · Planning cell {number:05d}",
            "region": region,
            "demand": demand,
            "traffic": traffic,
            "ev_adoption": ev,
            "nearby_supply": supply,
            "access": access,
            "population_density": population,
            "bev_growth": bev_growth,
            "confidence": confidence,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "training_label": label,
            "opportunity": "Synthetic screening profile; validate demand and local charging coverage.",
            "validation_note": "Verify station inventory, dwell demand, grid capacity, land access and permitting.",
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=22000)
    parser.add_argument("--seed", type=int, default=20261119)
    parser.add_argument("--output", type=Path, default=Path("data/candidates.csv"))
    args = parser.parse_args()
    if args.rows < 100 or args.rows > 1000000:
        parser.error("--rows must be between 100 and 1,000,000")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(create_rows(args.rows, args.seed))
    print(f"Wrote {args.rows:,} synthetic planning cells to {args.output}")


if __name__ == "__main__":
    main()
