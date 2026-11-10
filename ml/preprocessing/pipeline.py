"""
EcoCycle AI — Causal Preprocessing & Feature Engineering Module
Task 2K Implementation
"""
import numpy as np
import pandas as pd

from ml.models.feature_engineering import generate_causal_features_for_battery
from ml.models.feature_schema import ADVANCED_FEATURE_COLUMNS


def prepare_inference_features(history_df: pd.DataFrame, preprocessor) -> pd.DataFrame:
    """Transform raw battery history and return the canonical 32 model features."""
    try:
        transformed = preprocessor.transform(history_df, is_train=False)
    except TypeError as exc:
        if not hasattr(preprocessor, "feature_names_in_"):
            raise exc
        transformed = None

    # The production artifact currently stores a sklearn scaler, while the
    # causal preprocessor used during feature generation returns a DataFrame.
    # Keep both artifact formats compatible without changing the inference
    # contract.
    if not isinstance(transformed, pd.DataFrame):
        transformed = history_df.copy()
        feature_names = getattr(preprocessor, "feature_names_in_", None)
        if feature_names is None:
            raise TypeError("Inference preprocessor must return a DataFrame.")
        transformed = transformed.sort_values(["battery_id", "cycle"]).reset_index(drop=True)
        transformed["IR_is_zero"] = (transformed["IR"] == 0.0).astype(int)
        transformed["temp_sensor_fault"] = (transformed["battery_id"] == 85).astype(int)
        for column in ("IR", "QCharge", "Tavg", "chargetime"):
            lag = transformed.groupby("battery_id")[column].shift(1)
            transformed[f"{column}_lag1"] = lag.fillna(transformed[column])
            transformed[f"{column}_delta"] = transformed[column] - transformed[f"{column}_lag1"]
        scaled = preprocessor.transform(transformed[list(feature_names)])
        transformed[list(feature_names)] = transformed[list(feature_names)].astype(float)
        transformed.loc[:, list(feature_names)] = scaled

    engineered = generate_causal_features_for_battery(transformed)
    return engineered[ADVANCED_FEATURE_COLUMNS].copy()


class CausalBatteryPreprocessor:
    def __init__(self):
        self.params = {}
        self.is_fitted = False

    def fit(self, train_df):
        train_raw = train_df.copy()
        # Non-zero IR median
        train_nonzero_ir = train_raw[train_raw["IR"] > 0.0]["IR"]
        train_median_ir = float(train_nonzero_ir.median())
        
        # Healthy temperature offsets (excluding Battery 85)
        train_healthy = train_raw[train_raw["battery_id"] != 85]
        delta_tmin = float((train_healthy["Tavg"] - train_healthy["Tmin"]).median())
        delta_tmax = float((train_healthy["Tmax"] - train_healthy["Tavg"]).median())
        train_healthy_median_tavg = float(train_healthy["Tavg"].median())
        train_healthy_median_tmin = float(train_healthy["Tmin"].median())
        
        self.params = {
            "train_median_ir": train_median_ir,
            "delta_tmin": delta_tmin,
            "delta_tmax": delta_tmax,
            "train_healthy_median_tavg": train_healthy_median_tavg,
            "train_healthy_median_tmin": train_healthy_median_tmin
        }
        self.is_fitted = True
        return self

    def transform(self, df_in, is_train=False):
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted on training data before transform.")
            
        df = df_in.sort_values(["battery_id", "cycle"]).copy().reset_index(drop=True)
        
        # Anomaly flags
        df["IR_is_zero"] = (df["IR"] == 0.0).astype(int)
        df["temp_sensor_fault"] = (df["battery_id"] == 85).astype(int)
        
        # Tmin == 0 causal ffill
        df["Tmin"] = df["Tmin"].replace(0.0, np.nan)
        df["Tmin"] = df.groupby("battery_id")["Tmin"].ffill()
        df["Tmin"] = df["Tmin"].fillna(self.params["train_healthy_median_tmin"])
        
        # Battery 85 temperature handling (only if present in partition)
        if 85 in df["battery_id"].values and is_train:
            b85_mask = df["battery_id"] == 85
            tavg_b85 = df.loc[b85_mask, "Tavg"].copy()
            tavg_b85 = tavg_b85.apply(lambda x: np.nan if x < 0 else x)
            tavg_b85 = tavg_b85.ffill().fillna(self.params["train_healthy_median_tavg"])
            df.loc[b85_mask, "Tavg"] = tavg_b85
            df.loc[b85_mask, "Tmin"] = df.loc[b85_mask, "Tavg"] - self.params["delta_tmin"]
            df.loc[b85_mask, "Tmax"] = df.loc[b85_mask, "Tavg"] + self.params["delta_tmax"]
            
        # Numerical IR
        df["IR"] = df["IR"].replace(0.0, np.nan)
        df["IR"] = df.groupby("battery_id")["IR"].ffill()
        df["IR"] = df["IR"].fillna(self.params["train_median_ir"])
        
        # Causal temporal features
        df["IR_lag1"] = df.groupby("battery_id")["IR"].shift(1).fillna(df["IR"])
        df["IR_delta"] = df["IR"] - df["IR_lag1"]
        
        df["QCharge_lag1"] = df.groupby("battery_id")["QCharge"].shift(1).fillna(df["QCharge"])
        df["QCharge_delta"] = df["QCharge"] - df["QCharge_lag1"]
        
        df["Tavg_lag1"] = df.groupby("battery_id")["Tavg"].shift(1).fillna(df["Tavg"])
        df["Tavg_delta"] = df["Tavg"] - df["Tavg_lag1"]
        
        df["chargetime_lag1"] = df.groupby("battery_id")["chargetime"].shift(1).fillna(df["chargetime"])
        df["chargetime_delta"] = df["chargetime"] - df["chargetime_lag1"]
        
        return df
