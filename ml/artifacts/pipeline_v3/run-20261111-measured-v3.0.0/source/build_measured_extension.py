"""Build separately governed measured cohorts; never pool incompatible tests."""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ml/data/sources/wheeler2025"
REPORT = ROOT / "reports/soh_extension"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_discharge_labels(data):
    """Reject absent, degraded-start, duplicate, or inconsistent references."""
    required = ["battery_id", "cycle", "QDischarge", "reference_capacity_Ah", "reference_cycle", "SOH"]
    if data[required].isna().any().any():
        raise ValueError("Missing measured discharge/reference metadata")
    if data.duplicated(["battery_id", "cycle"]).any():
        raise ValueError("Duplicate battery/cycle")
    if not np.isfinite(data[["cycle", "QDischarge", "reference_capacity_Ah", "reference_cycle", "SOH"]]).all().all():
        raise ValueError("Nonfinite discharge/reference")
    if (data.QDischarge <= 0).any() or (data.reference_capacity_Ah <= 0).any():
        raise ValueError("Positive measured discharge/reference required")
    if (data.reference_cycle != 0).any():
        raise ValueError("This source requires the documented pristine cycle-0 characterization")
    for _, group in data.groupby("battery_id"):
        birth = group[group.cycle == 0]
        if len(birth) != 1 or group.reference_capacity_Ah.nunique() != 1:
            raise ValueError("Missing or inconsistent pristine cycle-0 reference")
        if not np.isclose(birth.QDischarge.iloc[0], group.reference_capacity_Ah.iloc[0], atol=1e-12, rtol=0):
            raise ValueError("Reference must equal measured cycle-0 discharge, never charge")
    expected = 100 * data.QDischarge / data.reference_capacity_Ah
    if not np.allclose(data.SOH, expected, atol=1e-9, rtol=0):
        raise ValueError("SOH differs from measured discharge/reference ratio")


def coverage(data):
    result = {"rows": len(data), "independent_batteries": data.battery_id.nunique(),
              "soh_min": float(data.SOH.min()), "soh_max": float(data.SOH.max()), "ranges": {}}
    for low, high in [(0, 50), (50, 60), (60, 70), (70, 80), (80, 110)]:
        group = data[(data.SOH >= low) & (data.SOH < high)]
        result["ranges"][f"[{low},{high})"] = {"rows": len(group), "independent_batteries": group.battery_id.nunique()}
    return result


def main():
    REPORT.mkdir(exist_ok=True)
    metadata = json.loads((SOURCE / "dataset_metadata.json").read_text(encoding="utf-8"))["data"]["latestVersion"]
    if (metadata["versionNumber"], metadata["versionMinorNumber"]) != (2, 0):
        raise ValueError("Source must be the verified V2.0 release")
    if "creativecommons.org/licenses/by/4.0" not in metadata.get("termsOfUse", ""):
        raise ValueError("Verified CC BY 4.0 source terms required")
    source = pd.read_csv(SOURCE / "discharge_measurements.csv")
    excluded = source[source.status != "ok"].copy()
    data = source[source.status == "ok"].copy()
    # Source cycle 0 is explicitly the pristine, post-wake-up 50C C/3 test.
    # Never select an arbitrary first available observation for a reference.
    reference = data[data.cycle == 0].set_index("source_cell_id")
    if reference.index.duplicated().any() or set(data.source_cell_id) != set(reference.index):
        raise ValueError("Every cell requires exactly one pristine cycle-0 discharge")
    data["battery_id"] = "wheeler2025:" + data.source_cell_id
    data["reference_capacity_Ah"] = data.source_cell_id.map(reference.QDischarge)
    data["reference_source_sha256"] = data.source_cell_id.map(reference.source_sha256)
    data["reference_entry"] = data.source_cell_id.map(reference.source_entry)
    data["reference_cycle"] = 0
    data["SOH"] = 100 * data.QDischarge / data.reference_capacity_Ah
    data["source_id"] = "wheeler2025"
    data["source_doi"] = "10.57745/OLBXKT"
    data["source_version"] = "2.0"
    data["license"] = "CC-BY-4.0"
    data["chemistry"] = "LFP/graphite"
    data["nominal_capacity_Ah"] = 1.1
    data["protocol"] = "wheeler_C3_50C"
    data["chamber_temperature_C"] = 50
    data["cell_temperature_measured"] = False
    data["test_group"] = data.source_cell_id.str.extract(r"Cell(\d+)")[0].astype(int)
    data["reference_method"] = "measured pristine cycle-0 C/3 discharge at 50C, after 25 wake-up cycles"
    validate_discharge_labels(data)
    # Distinct physical measurements cannot masquerade under several IDs.
    if data.source_sha256.duplicated().any():
        raise ValueError("Duplicate source measurement content")
    output = ROOT / "ml/data/wheeler2025_discharge_measured.csv"
    with output.open("x", encoding="utf-8", newline="") as stream:
        data.to_csv(stream, index=False)
    original = ROOT / "ml/data/master_dataset.csv"
    extended = ROOT / "ml/data/master_dataset_extended.csv"
    if extended.exists():
        raise FileExistsError(extended)
    # No compatible low-SOH source was verified for Severson's sensor/protocol
    # contract. Publish an honest unchanged compatible cohort, separately.
    shutil.copyfile(original, extended)
    legacy = pd.read_csv(original)
    refs = legacy[legacy.cycle <= 50].groupby("battery_id").QDischarge.agg(["mean", "size"])
    refs.columns = ["reference_capacity_Ah", "reference_observations"]
    refs["source_id"] = "severson2019_existing"
    refs["global_battery_id"] = [f"severson2019:{bid}" for bid in refs.index]
    refs["reference_method"] = "existing mean measured discharge capacity at recorded cycles <=50; retained exactly"
    refs["source_license_status"] = "not independently reverified; existing data retained, no added source relicensing"
    refs.to_csv(REPORT / "existing_battery_references.csv")
    excluded.to_csv(REPORT / "excluded_characterizations.csv", index=False)
    summary = {"compatible_master": coverage(legacy), "separate_wheeler_cohort": coverage(data),
        "total_distinct_source_batteries_unpooled": legacy.battery_id.nunique() + data.battery_id.nunique(),
        "master_extended_sha256": digest(extended), "master_original_sha256": digest(original),
        "separate_measured_sha256": digest(output), "excluded_rows": len(excluded),
        "pooled_training": False, "compatible_master_extended": False,
        "reason": "50C accelerated aging; C/3 characterization instead of fast-charge/4C cycling; no cell temperature or per-cycle IR; distinct reference protocol. Kept separate.",
        "second_life_RUL": "Unavailable: no justified application-specific second-life endpoint; recording ends are censored, never failure.",
        "sampling": "Fixed in fetch script before extracting discharge labels: cycle 0, every 400 cycles and last characterization. No interpolation or relabeling."}
    (REPORT / "coverage.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
