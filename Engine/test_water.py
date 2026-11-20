"""
Tests for water.py.
Run from the engine folder with:  python -m pytest -v
"""

import pytest
from water import fit_line, days_until_limit, water_state, build_water


def test_fit_line_on_a_perfect_line():
    slope, intercept = fit_line([1, 3, 5, 7])      # +2 per day, starting at 1
    assert slope == pytest.approx(2)
    assert intercept == pytest.approx(1)


def test_fit_line_needs_two_readings():
    with pytest.raises(ValueError):
        fit_line([2.0])


def test_days_until_limit_on_a_perfect_line():
    # Today (day 3) is 7; +2 per day; limit 12 -> 2.5 days -> rounded DOWN to 2.
    assert days_until_limit([1, 3, 5, 7], limit=12) == 2


def test_already_unsafe_is_zero_days():
    assert days_until_limit([1, 3, 5, 13], limit=12) == 0


def test_flat_or_improving_water_has_no_prediction():
    assert days_until_limit([3, 3, 3, 3], limit=12) is None
    assert days_until_limit([5, 4, 3, 2], limit=12) is None


def test_noise_does_not_break_the_trend():
    # A single odd reading shouldn't flip a rising trend.
    assert days_until_limit([1, 2, 2.5, 1.8, 3, 3.6, 4], limit=10) is not None


def test_states():
    assert water_state(0) == "unsafe"
    assert water_state(3) == "warning"
    assert water_state(30) == "ok"
    assert water_state(None) == "ok"


def test_real_log_predicts_a_warning():
    w = build_water()
    assert w["state"] == "warning"
    assert w["days_to_limit"] == 3
    assert w["trend_ntu_per_day"] > 0


def test_status_json_includes_water():
    from grid_engine import build_status
    assert build_status()["water"]["recycler"] == "Recycler 12"
