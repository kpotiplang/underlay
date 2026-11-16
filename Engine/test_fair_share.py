"""
Tests for fair_share.py.
Run from the engine folder with:  python -m pytest -v
"""

import pytest
from fair_share import water_fill, unmet_need


def test_example_from_the_docstring():
    # 90 MW, needs 10/50/60 -> A gets all it needs, B and C split the rest.
    result = water_fill(90, {"A": 10, "B": 50, "C": 60})
    assert result["A"] == pytest.approx(10)
    assert result["B"] == pytest.approx(40)
    assert result["C"] == pytest.approx(40)


def test_enough_for_everyone():
    # Plenty of supply: everyone gets exactly what they need, no more.
    result = water_fill(1000, {"A": 10, "B": 50, "C": 60})
    assert result == pytest.approx({"A": 10, "B": 50, "C": 60})


def test_equal_needs_get_equal_shares():
    result = water_fill(30, {"A": 20, "B": 20, "C": 20})
    assert result == pytest.approx({"A": 10, "B": 10, "C": 10})


def test_never_gives_out_more_than_supply():
    needs = {"L12": 5, "L20": 40, "L33": 18, "L40": 75, "L41": 3}
    result = water_fill(100, needs)
    assert sum(result.values()) <= 100 + 1e-9


def test_nobody_gets_more_than_they_need():
    needs = {"L12": 5, "L20": 40, "L33": 18, "L40": 75, "L41": 3}
    result = water_fill(100, needs)
    for name in needs:
        assert result[name] <= needs[name] + 1e-9


def test_zero_supply_gives_everyone_zero():
    result = water_fill(0, {"A": 10, "B": 20})
    assert result == pytest.approx({"A": 0, "B": 0})


def test_no_levels_returns_empty():
    assert water_fill(50, {}) == {}


def test_a_level_needing_nothing_gets_nothing():
    result = water_fill(30, {"A": 0, "B": 50})
    assert result["A"] == pytest.approx(0)
    assert result["B"] == pytest.approx(30)  # all the supply goes to B


def test_order_of_input_does_not_matter():
    a = water_fill(90, {"A": 10, "B": 50, "C": 60})
    b = water_fill(90, {"C": 60, "A": 10, "B": 50})
    assert a == pytest.approx(b)


def test_negative_supply_is_rejected():
    with pytest.raises(ValueError):
        water_fill(-5, {"A": 10})


def test_negative_need_is_rejected():
    with pytest.raises(ValueError):
        water_fill(10, {"A": -1})


def test_unmet_need():
    needs = {"A": 10, "B": 50, "C": 60}
    result = water_fill(90, needs)
    assert unmet_need(result, needs) == pytest.approx({"A": 0, "B": 10, "C": 20})
