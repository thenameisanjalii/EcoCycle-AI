"""
EcoCycle AI — Causal Preprocessing & Feature Engineering Module
Task 2K Implementation
"""
import numpy as np
import pandas as pd

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
