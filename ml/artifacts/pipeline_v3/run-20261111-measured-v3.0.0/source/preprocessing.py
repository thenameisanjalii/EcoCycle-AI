"""Measured C/3 charge features; discharge and birth reference are labels only."""
import numpy as np
import pandas as pd

RAW = ["QCharge", "chargetime", "cycle"]
SINGLE_FEATURES = RAW
HISTORY_FEATURES = RAW + ["history_count", "observed_span", "cycle_gap"] + [
    f"{column}_{suffix}" for column in ["QCharge", "chargetime"]
    for suffix in ["lag1", "delta_per_cycle", "past_mean5", "past_std5"]]
DOMAIN = "wheeler_C3_50C"


def validate_raw(frame, history=False):
    data = frame.copy()
    unknown = set(data) - set(RAW + ["battery_id", "row_id"])
    if unknown:
        raise ValueError(f"Unsupported or leakage fields: {sorted(unknown)}")
    if data.empty or not set(RAW).issubset(data):
        raise ValueError("Measured QCharge (Ah), chargetime (minutes), and cycle required")
    for column in RAW:
        data[column] = pd.to_numeric(data[column], errors="raise").astype(float)
    if not np.isfinite(data[RAW]).all().all():
        raise ValueError("Finite measurements required; no guessed sensors")
    if ((data.QCharge <= 0) | (data.QCharge > 2) | (data.chargetime <= 0)
        | (data.chargetime > 10000) | (data.cycle < 0) | (data.cycle > 100000)
        | (data.cycle % 1 != 0)).any():
        raise ValueError("Measurement outside physical/protocol bounds")
    if history:
        if "battery_id" not in data or data.battery_id.isna().any():
            raise ValueError("History requires battery IDs")
        data["battery_id"] = data.battery_id.astype(str)
        if data.duplicated(["battery_id", "cycle"]).any():
            raise ValueError("Duplicate battery cycles")
    return data


class MeasurementPreprocessor:
    def fit(self, raw):
        data = validate_raw(raw)
        self.support = {column: [float(data[column].min()), float(data[column].max())] for column in RAW}
        return self

    def transform(self, raw, contract="single"):
        if contract not in {"single", "history"}:
            raise ValueError("Unknown contract")
        if not hasattr(self, "support"):
            raise ValueError("Fit on training batteries first")
        data = validate_raw(raw, history=contract == "history").reset_index(drop=True)
        if contract == "history":
            data = data.sort_values(["battery_id", "cycle"], kind="stable")
        features = data[RAW].copy()
        if contract == "history":
            groups = data.groupby("battery_id", sort=False)
            features["history_count"] = groups.cumcount()
            features["observed_span"] = data.cycle - groups.cycle.transform("first")
            features["cycle_gap"] = groups.cycle.diff()
            for column in ["QCharge", "chargetime"]:
                grouped = groups[column]
                lag = grouped.shift(1)
                features[f"{column}_lag1"] = lag
                features[f"{column}_delta_per_cycle"] = (data[column] - lag) / features.cycle_gap
                features[f"{column}_past_mean5"] = grouped.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
                features[f"{column}_past_std5"] = grouped.transform(lambda s: s.shift(1).rolling(5, min_periods=2).std())
        return features[HISTORY_FEATURES if contract == "history" else SINGLE_FEATURES].sort_index()

    def reliability(self, raw):
        data = validate_raw(raw)
        return [[f"{column}_outside_training_support" for column, (low, high) in self.support.items()
                 if not low <= row[column] <= high] for _, row in data.iterrows()]
