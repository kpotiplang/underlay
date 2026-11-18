"""
Tests for space.py.
Run from the engine folder with:  python -m pytest -v
"""

import pytest
from space import families_in_room, build_space, SEALED_ROOMS


def test_room_rounds_down():
    assert families_in_room(14, 6) == 2   # 14 / 6 = 2.33 -> 2 families
    assert families_in_room(12, 6) == 2   # exactly 2


def test_room_too_small_houses_nobody():
    assert families_in_room(5, 6) == 0


def test_bad_inputs_are_rejected():
    with pytest.raises(ValueError):
        families_in_room(-1)
    with pytest.raises(ValueError):
        families_in_room(10, 0)


def test_totals_add_up():
    rooms = [{"id": "a", "area_m2": 12, "years_empty": 1, "behind_plate": True},
             {"id": "b", "area_m2": 7, "years_empty": 2, "behind_plate": False}]
    s = build_space(rooms, crowded=10, m2_per_family=6)
    assert s["families_housed"] == 3      # 2 + 1
    assert s["sealed_area_m2"] == 19
    assert s["still_crowded"] == 7
    assert [r["id"] for r in s["behind_plate"]] == ["a"]


def test_still_crowded_never_negative():
    rooms = [{"id": "big", "area_m2": 600, "years_empty": 1, "behind_plate": False}]
    assert build_space(rooms, crowded=10)["still_crowded"] == 0


def test_no_rooms():
    s = build_space([], crowded=5)
    assert s["families_housed"] == 0 and s["behind_plate"] == []


def test_real_record_has_rooms_to_draw():
    s = build_space()
    assert 1 <= len(s["behind_plate"]) <= 3    # the AR page has 3 room slots
    assert s["families_housed"] > 0


def test_build_space_does_not_change_the_record():
    build_space()["behind_plate"][0]["area_m2"] = 999
    assert SEALED_ROOMS[0]["area_m2"] == 14


def test_status_json_includes_space():
    from grid_engine import build_status
    assert build_status()["space"]["sealed_rooms"] == len(SEALED_ROOMS)
