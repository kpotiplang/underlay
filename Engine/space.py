"""
space.py - finds sealed, empty rooms on Level 40 and how many crowded families they could house.

The Directorate keeps these rooms "off the record" while families share single rooms.
This is a SIMULATED building record (we have no real Hollow). The rule is simple and real:
a family needs at least M2_PER_FAMILY square meters, so a sealed room can house
area // M2_PER_FAMILY families (rounded down - you can't split a family across rooms).
"""

M2_PER_FAMILY = 6          # minimum floor space for one family, in square meters
CROWDED_FAMILIES = 310     # families on L40 currently sharing a single room with another family

# Simulated building record for Level 40.
# behind_plate: True if the room sits behind wall plate L40-C (the AR page draws these).
SEALED_ROOMS = [
    {"id": "L40-C-07", "area_m2": 14, "years_empty": 6,  "behind_plate": True},
    {"id": "L40-C-09", "area_m2": 22, "years_empty": 11, "behind_plate": True},
    {"id": "L40-C-12", "area_m2": 9,  "years_empty": 3,  "behind_plate": True},
    {"id": "L40-A-02", "area_m2": 18, "years_empty": 8,  "behind_plate": False},
    {"id": "L40-A-05", "area_m2": 12, "years_empty": 4,  "behind_plate": False},
    {"id": "L40-B-01", "area_m2": 30, "years_empty": 14, "behind_plate": False},
    {"id": "L40-B-03", "area_m2": 8,  "years_empty": 2,  "behind_plate": False},
    {"id": "L40-B-08", "area_m2": 16, "years_empty": 9,  "behind_plate": False},
    {"id": "L40-D-04", "area_m2": 25, "years_empty": 12, "behind_plate": False},
    {"id": "L40-D-06", "area_m2": 11, "years_empty": 5,  "behind_plate": False},
    {"id": "L40-D-10", "area_m2": 20, "years_empty": 7,  "behind_plate": False},
    {"id": "L40-E-02", "area_m2": 13, "years_empty": 10, "behind_plate": False},
]


def families_in_room(area_m2, m2_per_family=M2_PER_FAMILY):
    """How many families fit in one room. Rounded down: 14 m2 at 6 m2/family -> 2 families."""
    if area_m2 < 0:
        raise ValueError("room area can't be negative")
    if m2_per_family <= 0:
        raise ValueError("space per family must be more than 0")
    return int(area_m2 // m2_per_family)


def build_space(rooms=SEALED_ROOMS, crowded=CROWDED_FAMILIES, m2_per_family=M2_PER_FAMILY):
    """Summary the AR page reads: totals for the level, plus the rooms behind this plate."""
    housed = sum(families_in_room(r["area_m2"], m2_per_family) for r in rooms)
    return {
        "sealed_rooms": len(rooms),
        "sealed_area_m2": sum(r["area_m2"] for r in rooms),
        "families_housed": housed,
        "crowded_families": crowded,
        # Can't house more families than are actually crowded.
        "still_crowded": max(0, crowded - housed),
        "m2_per_family": m2_per_family,
        "behind_plate": [dict(r) for r in rooms if r["behind_plate"]],
        "note": "Simulated building record. The housing rule is real.",
    }


if __name__ == "__main__":
    s = build_space()
    print(f"Sealed rooms on L40: {s['sealed_rooms']} ({s['sealed_area_m2']} m2)")
    print(f"Could house {s['families_housed']} of {s['crowded_families']} crowded families "
          f"at {s['m2_per_family']} m2 per family")
    for r in s["behind_plate"]:
        print(f"  behind plate: {r['id']}  {r['area_m2']} m2, empty {r['years_empty']} years")
