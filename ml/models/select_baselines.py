"""
EcoCycle AI — Baseline Model Selection Module (Task 2L.3 Phase A)
Locks the winning baseline models based strictly on lowest Validation RMSE.
Test data is NEVER accessed during selection.
"""
import os
import pandas as pd

def select_best_baseline_models(results_csv_path):
    """
    Ranks baseline models strictly by validation RMSE and returns the winning models.
    """
    df = pd.read_csv(results_csv_path)
    
    soh_df = df[df["target"] == "SOH"].sort_values("rmse", ascending=True).reset_index(drop=True)
    rul_df = df[df["target"] == "RUL"].sort_values("rmse", ascending=True).reset_index(drop=True)
    
    soh_winner = soh_df.iloc[0]
    rul_winner = rul_df.iloc[0]
    
    selection_record = {
        "SOH": {
            "model_name": soh_winner["model"],
            "val_rmse": float(soh_winner["rmse"]),
            "val_mae": float(soh_winner["mae"]),
            "val_r2": float(soh_winner["r2"]),
            "selection_criterion": "Lowest Validation RMSE"
        },
        "RUL": {
            "model_name": rul_winner["model"],
            "val_rmse": float(rul_winner["rmse"]),
            "val_mae": float(rul_winner["mae"]),
            "val_r2": float(rul_winner["r2"]),
            "selection_criterion": "Lowest Validation RMSE"
        }
    }
    return selection_record, soh_df, rul_df
