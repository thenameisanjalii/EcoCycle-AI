"""Selection must preserve source rows and supply distinct measured cycles."""
import pandas as pd
import pytest

from get_demo_data import select_test_cases


def test_preceding_observation_and_chronological_order():
    source = pd.DataFrame([
        {"battery_id": 1, "cycle": 30, "SOH": 79.99, "IR": 0.03},
        {"battery_id": 1, "cycle": 10, "SOH": 90, "IR": 0.01},
        {"battery_id": 1, "cycle": 20, "SOH": 85, "IR": 0.02},
        {"battery_id": 1, "cycle": 40, "SOH": 75, "IR": 0.04},
    ])
    result = select_test_cases(source, [1], battery_count=1)
    pd.testing.assert_frame_equal(result, source.iloc[[2, 0]].reset_index(drop=True))


def test_first_observation_uses_next_real_cycle_without_synthesizing_history():
    source = pd.DataFrame([
        {"battery_id": 2, "cycle": 15, "SOH": 80},
        {"battery_id": 2, "cycle": 21, "SOH": 79},
    ])
    pd.testing.assert_frame_equal(select_test_cases(source, [2], 1), source)


def test_excludes_training_batteries_and_singletons_and_ranks_eligible_batteries():
    source = pd.DataFrame([
        {"battery_id": bid, "cycle": cycle, "SOH": soh}
        for bid, values in [(1, [80, 80]), (2, [90, 89]), (3, [82, 81]), (4, [80])]
        for cycle, soh in enumerate(values, start=1)
    ])
    result = select_test_cases(source, [2, 3, 4], 1)
    assert result.battery_id.tolist() == [3, 3]
    with pytest.raises(ValueError, match="eligible held-out"):
        select_test_cases(source, [2, 3, 4], 3)


def test_duplicate_cycles_rejected():
    source = pd.DataFrame([{"battery_id": 1, "cycle": 1, "SOH": 80}] * 2)
    with pytest.raises(ValueError, match="duplicate battery cycles"):
        select_test_cases(source, [1], 1)


def test_ties_are_deterministic_when_source_order_changes():
    source = pd.DataFrame([
        {"battery_id": bid, "cycle": cycle, "SOH": 80}
        for bid in [1, 2] for cycle in [1, 2, 3]
    ])
    expected = select_test_cases(source, [1, 2], 2)
    actual = select_test_cases(source.sample(frac=1, random_state=7), [1, 2], 2)
    pd.testing.assert_frame_equal(actual, expected)
