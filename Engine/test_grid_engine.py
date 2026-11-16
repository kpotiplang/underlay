"""
Tests for grid_engine.py.
Run from the engine folder with:  python -m pytest -v
"""

import pytest
from grid_engine import (build_status, directorate_split, essential_need_mw,
                         people_at_risk, MIN_RATION_MW)


def make_levels():
    """A tiny made-up district, so tests don't depend on the real LEVELS table."""
    return [
        {"name": "A", "depth": 12, "population": 1000, "request_mw": 20, "need_mw": 2.5},
        {"name": "B", "depth": 40, "population": 1000, "request_mw": 3.9, "need_mw": 3.9},
    ]


def test_deeper_levels_need_more_per_person():
    shallow = essential_need_mw({"depth": 12, "population": 1000})
    deep = essential_need_mw({"depth": 40, "population": 1000})
    assert deep > shallow


def test_directorate_never_exceeds_supply():
    split = directorate_split(10, make_levels())
    assert sum(split.values()) <= 10 + 1e-9


def test_directorate_gives_everyone_the_minimum_when_possible():
    split = directorate_split(10, make_levels())
    for mw in split.values():
        assert mw >= MIN_RATION_MW - 1e-9


def test_directorate_serves_upper_level_first():
    # A (upper) asks for 20 and gets everything after rations; B stays at the minimum.
    split = directorate_split(10, make_levels())
    assert split["A"] == pytest.approx(10 - MIN_RATION_MW)
    assert split["B"] == pytest.approx(MIN_RATION_MW)


def test_directorate_splits_equally_if_supply_is_below_rations():
    split = directorate_split(2, make_levels())
    assert split["A"] == pytest.approx(1)
    assert split["B"] == pytest.approx(1)


def test_directorate_with_zero_supply():
    split = directorate_split(0, make_levels())
    assert sum(split.values()) == pytest.approx(0)


def test_people_at_risk_zero_when_needs_met():
    levels = make_levels()
    assert people_at_risk({"A": 2.5, "B": 3.9}, levels) == 0


def test_people_at_risk_counts_shortfall():
    levels = make_levels()
    # B gets half its need -> half of its 1000 people at risk.
    assert people_at_risk({"A": 2.5, "B": 1.95}, levels) == 500


def test_fair_split_puts_fewer_people_at_risk():
    status = build_status()
    assert (status["modes"]["fair"]["people_at_risk"]
            < status["modes"]["directorate"]["people_at_risk"])


def test_status_has_what_the_ar_page_reads():
    status = build_status()
    for mode in ("directorate", "fair"):
        s = status["modes"][mode]
        assert set(s) >= {"allocation_mw", "share_to_upper_pct",
                          "share_to_viewer_pct", "people_at_risk"}
        assert sum(s["allocation_mw"].values()) <= status["supply_mw"] + 0.05


def test_build_status_does_not_change_the_original_table():
    from grid_engine import LEVELS
    build_status()
    assert LEVELS[2]["request_mw"] is None  # still unset; only the copy was filled in


def test_huge_supply_means_nobody_at_risk_either_way():
    status = build_status(supply=10_000)
    assert status["modes"]["fair"]["people_at_risk"] == 0
    assert status["modes"]["directorate"]["people_at_risk"] == 0
