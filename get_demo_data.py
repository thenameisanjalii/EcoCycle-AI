"""Generate two genuine observations for each of twenty held-out batteries.

Run from the project folder: python get_demo_data.py
Use the observation closest to 80% measured SOH and its preceding recorded
cycle. If it is the first observation, use the next recorded cycle instead.
Each per-battery CSV is chronological and can be submitted as history.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "ml/data/master_dataset.csv"
BUNDLE = ROOT / "ml/artifacts/pipeline_v2/run-20261111-v2.0.1"
OUTPUT = ROOT / "presentation_test_cases.csv"
INPUT_DIR = ROOT / "presentation_inputs"
BATTERY_COUNT = 20
CASES_PER_BATTERY = 2
FRONTEND_FIELDS = [
    "IR", "QCharge", "Tavg", "Tmax", "Tmin", "chargetime", "cycle", "battery_id"
]
SELECTION = (
    "Twenty held-out batteries whose closest recorded SOH is nearest 80%. "
    "For each, select that observation and the immediately preceding recorded "
    "cycle; use the following recorded cycle if the closest observation is "
    "the first. Sort each pair chronologically. No prediction-based selection."
)


def select_test_cases(df, test_ids, battery_count=BATTERY_COUNT):
    """Return two unmodified, distinct source rows per selected battery."""
    held_out = df[df["battery_id"].isin(test_ids)].copy()
    if held_out.duplicated(["battery_id", "cycle"]).any():
        raise ValueError("Source contains duplicate battery cycles.")
    held_out = held_out.sort_values(["battery_id", "cycle"], kind="stable")
    held_out = held_out.groupby("battery_id", sort=False).filter(
        lambda group: len(group) >= CASES_PER_BATTERY
    )
    if held_out[["SOH", "cycle"]].isna().any().any():
        raise ValueError("Source SOH and cycle must be present for selection.")
    anchors = (
        held_out.assign(_distance_to_80=(held_out["SOH"] - 80).abs())
        .sort_values(["battery_id", "_distance_to_80", "cycle"], kind="stable")
        .drop_duplicates(subset=["battery_id"])
        .sort_values(["_distance_to_80", "battery_id"], kind="stable")
        .head(battery_count)
    )
    if len(anchors) != battery_count:
        raise ValueError(f"Only {len(anchors)} eligible held-out batteries; need {battery_count}.")

    pairs = []
    for bid, anchor_cycle in anchors[["battery_id", "cycle"]].itertuples(index=False, name=None):
        history = held_out.loc[held_out.battery_id == bid]
        position = int(history.cycle.eq(anchor_cycle).to_numpy().nonzero()[0][0])
        positions = [position - 1, position] if position > 0 else [0, 1]
        pairs.append(history.iloc[positions])
    return pd.concat(pairs, ignore_index=True)


def write_generated(path, content):
    """Refresh this generator's outputs; identical reruns leave files untouched."""
    encoded = content.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return
    path.write_bytes(encoded)


def main():
    source_hash = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    registry = json.loads((BUNDLE / "registry.json").read_text(encoding="utf-8"))
    if source_hash != registry["dataset_sha256"]:
        raise ValueError("Dataset does not match the saved v2 model's training source.")
    df = pd.read_csv(DATASET)
    test_ids = json.loads((BUNDLE / "splits.json").read_text(encoding="utf-8"))["test"]
    test_cases = select_test_cases(df, test_ids)
    counts = test_cases.groupby("battery_id").size()
    if len(counts) != BATTERY_COUNT or not counts.eq(CASES_PER_BATTERY).all():
        raise ValueError("Expected exactly two observations for each selected battery.")
    if hashlib.sha256(DATASET.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Source dataset changed during extraction.")

    INPUT_DIR.mkdir(exist_ok=True)
    write_generated(OUTPUT, test_cases.to_csv(index=False))
    for bid, history in test_cases.groupby("battery_id", sort=False):
        inputs = history.loc[:, FRONTEND_FIELDS]
        write_generated(INPUT_DIR / f"battery_{int(bid)}_near_80_soh.csv", inputs.to_csv(index=False))

    metadata = {
        "dataset": DATASET.relative_to(ROOT).as_posix(),
        "dataset_sha256": source_hash,
        "bundle": BUNDLE.relative_to(ROOT).as_posix(),
        "selection": SELECTION,
        "cases_per_battery": CASES_PER_BATTERY,
        "total_cases": len(test_cases),
        "battery_ids": [int(bid) for bid in test_cases.battery_id.drop_duplicates()],
        "cases": [
            {"battery_id": int(row.battery_id), "cycle": float(row.cycle), "measured_soh": float(row.SOH)}
            for row in test_cases.itertuples(index=False)
        ],
        "rows_changed": False,
        "notes": [
            "Full extracted rows retain SOH, QDischarge and legacy RUL for reference only; not an inference upload.",
            "Legacy RUL is cycles to recording end, not observed second-life service failure.",
            "Import one presentation_inputs CSV at a time: each contains two distinct observed cycles from one battery.",
            "The API estimates SOH and, when available, RUL for the latest of the two submitted cycles.",
            "Measured SOH near 80% does not guarantee a model prediction of exactly 80%.",
            "Zero IR readings and all other source measurements remain unchanged.",
        ],
    }
    write_generated(INPUT_DIR / "provenance.json", json.dumps(metadata, indent=2) + "\n")
    write_generated(INPUT_DIR / "README.md", """# Presentation inputs closest to 80% measured SOH

Generated by `python get_demo_data.py` from the exact master CSV used by the
saved v2 models. There are 40 genuine observations: two per battery for the
same twenty held-out battery IDs selected by proximity to 80% measured SOH.
No measurements or labels are synthesized or modified.

Each battery's pair contains its observation closest to 80% measured SOH
and the preceding recorded cycle. If the closest observation is its first,
the next recorded cycle is used instead. Pairs are ordered chronologically;
recorded cycle numbers need not be consecutive. See provenance.json for the
source hash, selected IDs, cycles, measured SOH and selection rule.

Import one battery_*.csv at a time into the frontend. Each contains two rows
with the eight accepted measurement fields, omitting SOH, RUL and QDischarge.
These are history inputs: the API returns the latest-cycle assessment and
can estimate RUL from the supplied observations. Missing RUL remains
unavailable; no value is substituted. Two observations provide limited
history; use the full observed history when available.

The root presentation_test_cases.csv contains the same 40 source rows with
all original columns and labels for reference. Do not upload it directly:
it contains multiple batteries and target/discharge columns.
Its legacy RUL is time to recording end, not second-life service failure.

Rerunning the script refreshes its generated CSVs, README and provenance.
The source dataset and saved model artifacts are never changed.
""")
    print(f"Generated {len(test_cases)} test cases: {CASES_PER_BATTERY} cycles x {BATTERY_COUNT} batteries.")
    print(test_cases[["battery_id", "cycle", "SOH"]].to_string(index=False))
    print(f"Reference data: {OUTPUT.relative_to(ROOT)}")
    print("Frontend-ready history: presentation_inputs/ (import one battery CSV at a time).")


if __name__ == "__main__":
    main()
