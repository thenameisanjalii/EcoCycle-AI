"""
EcoCycle AI — Input Validation & Leakage Protection Module
Task 2M.4 — Final Model Packaging & Inference Pipeline

Provides strict validation for inference inputs:
1. Rejects target leakage features (QDischarge, future-cycle info, cross-target ground truth)
2. Segregates metadata (battery_id, cycle, row_id) from predictive feature matrix X
3. Enforces presence of all 32 causal features
4. Validates data types, NaN values, infinite values, and physical admissibility bounds
5. Enforces deterministic feature ordering matching the trained model schemas
"""

from typing import Union, Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd

from .feature_schema import (
    ADVANCED_FEATURE_COLUMNS,
    FORBIDDEN_COLUMNS,
    FORBIDDEN_SOH_COLUMNS,
    FORBIDDEN_RUL_COLUMNS,
    METADATA_COLUMNS,
    PHYSICAL_VALUE_BOUNDS
)


class InputValidationError(ValueError):
    """Raised when inference input data is malformed, missing required features, or out of bounds."""
    pass


class DataLeakageError(ValueError):
    """Raised when forbidden target leakage, future lookahead, or cross-target labels enter input."""
    pass


def validate_inference_input(
    data: Union[Dict[str, Any], List[Dict[str, Any]], pd.Series, pd.DataFrame],
    target: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validates and standardizes input data for model inference.

    Args:
        data: Single dictionary, list of dictionaries, pandas Series, or pandas DataFrame.
        target: Optional target context ('soh', 'rul', or None for both).

    Returns:
        Tuple of:
            - X (pd.DataFrame): 32-feature matrix with deterministic column ordering (float64).
            - metadata (pd.DataFrame): Non-predictive metadata columns (e.g., battery_id, row_id).

    Raises:
        DataLeakageError: If forbidden target leakage or future features are present.
        InputValidationError: If features are missing, NaNs/Infs are present, or values are out of bounds.
    """
    # 1. Standardize input to a DataFrame copy
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, list):
        if len(data) == 0:
            raise InputValidationError("Input list of records is empty.")
        df = pd.DataFrame(data)
    elif isinstance(data, pd.Series):
        df = pd.DataFrame([data.to_dict()])
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise InputValidationError(
            f"Unsupported input type '{type(data)}'. Expected dict, list of dicts, pd.Series, or pd.DataFrame."
        )

    if len(df) == 0:
        raise InputValidationError("Input DataFrame has zero rows.")

    # 2. Strict Target Leakage & Anti-Cheat Validation
    col_names = set(df.columns)
    
    # Check general forbidden leakage columns (QDischarge, max_cycle, etc.)
    for forb in FORBIDDEN_COLUMNS:
        if forb in col_names:
            raise DataLeakageError(
                f"Data leakage detected! Forbidden column '{forb}' was provided in input data. "
                f"This feature directly leaks target or future lifespan information and is strictly prohibited."
            )

    # Check target-specific cross-leakage
    target_clean = target.lower().strip() if target else None
    if target_clean in ["soh", None]:
        if "RUL" in col_names or "predicted_rul" in col_names:
            raise DataLeakageError(
                "Cross-target leakage detected! Ground-truth 'RUL' cannot be provided when predicting SOH."
            )
    if target_clean in ["rul", None]:
        if "SOH" in col_names or "predicted_soh" in col_names:
            raise DataLeakageError(
                "Cross-target leakage detected! Ground-truth 'SOH' cannot be provided when predicting RUL."
            )

    # 3. Segregate non-predictive metadata (e.g., battery_id)
    metadata_cols_present = [c for c in df.columns if c in METADATA_COLUMNS or c.startswith("meta_")]
    metadata_df = df[metadata_cols_present].copy() if metadata_cols_present else pd.DataFrame(index=df.index)

    # 4. Feature Completeness Verification (32 Causal Features)
    missing_features = [f for f in ADVANCED_FEATURE_COLUMNS if f not in df.columns]
    if missing_features:
        raise InputValidationError(
            f"Input is missing {len(missing_features)} required causal feature(s):\n"
            f"{missing_features}\n"
            f"Expected full 32-feature causal schema."
        )

    # 5. Extract Feature Matrix in Exact Deterministic Order
    X = df[ADVANCED_FEATURE_COLUMNS].copy()

    # 6. Type Validation: Ensure all feature columns can be cast to float64
    for col in ADVANCED_FEATURE_COLUMNS:
        try:
            X[col] = pd.to_numeric(X[col], errors="raise").astype(np.float64)
        except Exception as e:
            raise InputValidationError(
                f"Feature '{col}' contains non-numeric data that cannot be converted to float: {e}"
            )

    # 7. NaN and Infinite Value Verification
    nan_counts = X.isna().sum()
    cols_with_nan = nan_counts[nan_counts > 0].to_dict()
    if cols_with_nan:
        raise InputValidationError(
            f"Input features contain NaN values in column(s): {cols_with_nan}. "
            f"Inference requires clean, non-null numeric inputs."
        )

    inf_mask = np.isinf(X.values)
    if inf_mask.any():
        inf_cols = [ADVANCED_FEATURE_COLUMNS[idx] for idx in np.where(inf_mask.any(axis=0))[0]]
        raise InputValidationError(
            f"Input features contain infinite values in column(s): {inf_cols}. "
            f"Inference requires finite numerical values."
        )

    # 8. Physical Admissibility Bounds Checking
    for col, (lower_bound, upper_bound) in PHYSICAL_VALUE_BOUNDS.items():
        if col in X.columns:
            vals = X[col].values
            if (vals < lower_bound).any() or (vals > upper_bound).any():
                invalid_min = vals.min()
                invalid_max = vals.max()
                raise InputValidationError(
                    f"Physical bound violation for feature '{col}'!\n"
                    f"Observed range: [{invalid_min:.4f}, {invalid_max:.4f}]\n"
                    f"Permissible range: [{lower_bound}, {upper_bound}]. "
                    f"Data indicates severe sensor anomaly, corrupted values, or impossible physical state."
                )

    return X, metadata_df
