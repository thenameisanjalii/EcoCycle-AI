"""
EcoCycle AI — Battery Grouped Splitting Module
Task 2K Implementation
"""
import numpy as np
import pandas as pd

def get_battery_splits(df, seed=42, train_fraction=0.70, validation_fraction=0.15):
    """
    Reproducible grouped partition, with counts derived from cohort size.
    Defaults reproduce the legacy split for the original 139-cell cohort.
    """
    unique_batteries = sorted(df["battery_id"].unique())
    if not (0 < train_fraction < 1 and 0 < validation_fraction < 1
            and train_fraction + validation_fraction < 1):
        raise ValueError("Split fractions must be positive and sum to less than one.")
    count = len(unique_batteries)
    if count < 3:
        raise ValueError("At least three batteries and nonempty partitions are required.")
    n_train = max(1, min(int(count * train_fraction), count - 2))
    n_val = max(1, min(int(round(count * validation_fraction)), count - n_train - 1))
    rng = np.random.RandomState(seed)
    shuffled = rng.permutation(unique_batteries)

    train_batteries = sorted(shuffled[:n_train])
    val_batteries   = sorted(shuffled[n_train:n_train + n_val])
    test_batteries  = sorted(shuffled[n_train + n_val:])
    
    return train_batteries, val_batteries, test_batteries
