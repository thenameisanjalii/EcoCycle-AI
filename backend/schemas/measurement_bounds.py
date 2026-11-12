"""Dataset limits shared with the prediction form."""
import json
import math
import re
from pathlib import Path

BOUNDS = json.loads((Path(__file__).resolve().parents[2] / "configs/prediction_input_bounds.json").read_text(encoding="utf-8"))["fields"]
DECIMAL = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$", re.ASCII)


def validate_measurement(field, value):
    bounds = BOUNDS[field]
    allowed = f"Allowed range: {bounds['min']} to {bounds['max']} {bounds['unit']}."
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{field} requires a finite number. {allowed}")
    if isinstance(value, str):
        value = value.strip()
        if not DECIMAL.fullmatch(value):
            raise ValueError(f"{field} requires a finite number. {allowed}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} requires a finite number. {allowed}")
    if value < bounds["min"] or value > bounds["max"]:
        raise ValueError(f"{field} is out of range. {allowed}")
    if field == "cycle" and not value.is_integer():
        raise ValueError(f"cycle must be a whole number. {allowed}")
    return value


def validate_battery_id(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Battery ID is required and must be a nonempty string or integer.")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise ValueError("Battery ID is required and must be nonempty.")
    return value
