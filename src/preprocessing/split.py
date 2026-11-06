"""
EcoCycle AI — Battery Grouped Splitting Module
Task 2K Implementation
"""
import numpy as np
import pandas as pd

def get_battery_splits(df, seed=42):
    """
    Reproduces the locked 70/15/15 battery-grouped partition.
    Returns:
        train_batteries (list of 97 ints)
        val_batteries   (list of 21 ints)
        test_batteries  (list of 21 ints)
    """
    unique_batteries = sorted(df["battery_id"].unique())
    rng = np.random.RandomState(seed)
    shuffled = rng.permutation(unique_batteries)

    train_batteries = sorted(shuffled[:97])
    val_batteries   = sorted(shuffled[97:118])
    test_batteries  = sorted(shuffled[118:])
    
    return train_batteries, val_batteries, test_batteries
