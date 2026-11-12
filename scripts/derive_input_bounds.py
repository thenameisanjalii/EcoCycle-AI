"""Derive public input limits from valid measurements in the master dataset."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "ml/data/master_dataset.csv"
OUTPUT = ROOT / "configs/prediction_input_bounds.json"
UNITS = {"IR": "ohms", "QCharge": "Ah", "Tavg": "°C", "Tmax": "°C", "Tmin": "°C", "chargetime": "minutes", "cycle": "cycles"}


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def derive_bounds():
    with DATASET.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    values = {field: [] for field in UNITS}
    for row in rows:
        readings = {field: number(row.get(field)) for field in UNITS}
        temperatures = [readings[field] for field in ("Tmin", "Tavg", "Tmax")]
        valid_temperatures = all(value is not None and 0 < value < 100 for value in temperatures)
        valid_temperatures = valid_temperatures and temperatures[0] <= temperatures[1] <= temperatures[2]
        for field, value in readings.items():
            if value is None or value <= 0:
                continue
            if field in ("Tmin", "Tavg", "Tmax") and not valid_temperatures:
                continue
            if field == "cycle" and not value.is_integer():
                continue
            values[field].append(value)
    return {
        "dataset": "ml/data/master_dataset.csv",
        "sha256": hashlib.sha256(DATASET.read_bytes()).hexdigest(),
        "rows": len(rows),
        "exclusions": "Nonfinite/missing and nonpositive readings; temperature triplets outside (0, 100) Celsius or with Tmin > Tavg or Tavg > Tmax; fractional cycles. Recorded charge-time holds and charge-capacity drift are retained.",
        "fields": {
            field: {"min": min(samples), "max": max(samples), "step": 1 if field == "cycle" else "any", "unit": UNITS[field], "excluded": len(rows) - len(samples)}
            for field, samples in values.items()
        },
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(derive_bounds(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT.relative_to(ROOT))
