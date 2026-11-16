"""
grid_engine.py - the simulated power grid of one Hollow district.

It answers one question two ways:
  "There's X MW of geothermal power today. Who gets it?"
    1. The Directorate's way: upper levels are served first, at whatever
       they ask for. Deep levels get a small minimum ration.
    2. The fair way: water-filling on what each level actually NEEDS
       (see fair_share.py).
Then it counts how many people are left without enough power under each,
and writes everything to status.json for the AR page to draw.

The numbers are SIMULATED (we have no real Hollow). The logic is real.

Run it from the engine folder:  python grid_engine.py
"""

import json
from pathlib import Path

from fair_share import water_fill, unmet_need

# ----------------------------------------------------------------------
# The district. Five levels, from the comfortable top to the hot bottom.
# request_mw: what the level ASKS the Directorate for. Upper levels ask
#             for far more than they need (lights, comfort, luxury).
#             For lower levels, request = need (they only ask to survive).
# ----------------------------------------------------------------------
LEVELS = [
    {"name": "L12", "depth": 12, "population": 2000, "request_mw": 30},
    {"name": "L20", "depth": 20, "population": 3500, "request_mw": 25},
    {"name": "L28", "depth": 28, "population": 5000, "request_mw": None},
    {"name": "L33", "depth": 33, "population": 6000, "request_mw": None},
    {"name": "L40", "depth": 40, "population": 4200, "request_mw": None},
]

SUPPLY_MW = 55             # today's geothermal output (a shortage day)
VIEWER_LEVEL = "L40"       # the level whose wall the phone is pointed at
UPPER_LEVEL_MAX_DEPTH = 20 # levels at depth 20 or above count as "upper"

KW_PER_PERSON = 2.5        # air fans + water pumps + basic light, per person
COOLING_PER_LEVEL = 0.02   # each level deeper adds 2% for cooling (it's hotter)
MIN_RATION_MW = 3          # the Directorate's minimum to every level


def essential_need_mw(level):
    """
    Power a level needs to keep people safe (air, water, cooling).
    WHY the cooling factor: the deeper you go, the hotter it gets
    (problem #3), so fans have to work harder per person.
    Level 12 is the baseline (factor 1.0).
    """
    cooling_factor = 1 + COOLING_PER_LEVEL * (level["depth"] - 12)
    kilowatts = level["population"] * KW_PER_PERSON * cooling_factor
    return kilowatts / 1000  # kW -> MW


def directorate_split(supply, levels):
    """
    The Directorate's rule, as residents describe it:
      1. Every level gets the same small minimum ration.
      2. What's left goes top-down: each level gets what it ASKS for
         until the power runs out.
    """
    allocation = {lvl["name"]: 0.0 for lvl in levels}
    if not levels:
        return allocation

    # Step 1: minimum ration. If there isn't even enough for that,
    # split what exists equally (nobody gets zero while others get some).
    ration = min(MIN_RATION_MW, supply / len(levels))
    for lvl in levels:
        allocation[lvl["name"]] = ration
    remaining = supply - ration * len(levels)

    # Step 2: top-down by request (smallest depth = highest level first).
    for lvl in sorted(levels, key=lambda l: l["depth"]):
        wanted_more = max(0, lvl["request_mw"] - allocation[lvl["name"]])
        given = min(wanted_more, remaining)
        allocation[lvl["name"]] += given
        remaining -= given

    return allocation


def people_at_risk(allocation, levels):
    """
    People who don't get enough power to be safe.
    WHY this formula: if a level gets 70% of its essential need, we treat
    30% of its people as at risk (their fans, pumps or cooling cut out).
    It's a simple, explainable estimate, not a medical prediction.
    """
    total = 0.0
    for lvl in levels:
        need = lvl["need_mw"]
        if need == 0:
            continue
        short = max(0, need - allocation[lvl["name"]])
        total += lvl["population"] * (short / need)
    return round(total)


def summarize(allocation, levels, supply, viewer):
    """Numbers the AR page shows: who gets what share, and how many are at risk."""
    upper_names = [l["name"] for l in levels if l["depth"] <= UPPER_LEVEL_MAX_DEPTH]
    to_upper = sum(allocation[n] for n in upper_names)
    return {
        "allocation_mw": {name: round(mw, 2) for name, mw in allocation.items()},
        "share_to_upper_pct": round(100 * to_upper / supply) if supply else 0,
        "share_to_viewer_pct": round(100 * allocation[viewer] / supply) if supply else 0,
        "people_at_risk": people_at_risk(allocation, levels),
    }


def build_status(supply=SUPPLY_MW, raw_levels=LEVELS, viewer=VIEWER_LEVEL):
    """Run both splits and package everything for the AR page."""
    # Fill in each level's need, and set request = need where it wasn't given.
    levels = []
    for raw in raw_levels:
        lvl = dict(raw)  # copy, so we never change the original LEVELS table
        lvl["need_mw"] = round(essential_need_mw(lvl), 2)
        if lvl["request_mw"] is None:
            lvl["request_mw"] = lvl["need_mw"]
        levels.append(lvl)

    needs = {lvl["name"]: lvl["need_mw"] for lvl in levels}
    directorate = directorate_split(supply, levels)
    fair = water_fill(supply, needs)

    return {
        "supply_mw": supply,
        "viewer_level": viewer,
        "levels": levels,
        "modes": {
            "directorate": summarize(directorate, levels, supply, viewer),
            "fair": summarize(fair, levels, supply, viewer),
        },
        "note": "Simulated data. The split rules and math are real.",
    }


def main():
    status = build_status()
    # status.json goes in the repo's top folder, next to index.html,
    # so GitHub Pages serves it to the phone.
    out_path = Path(__file__).resolve().parent.parent / "status.json"
    out_path.write_text(json.dumps(status, indent=2))

    # A readable table in the terminal - this is also good on-screen
    # material for the demo video.
    print(f"Supply today: {status['supply_mw']} MW\n")
    print(f"{'Level':<6}{'People':>8}{'Need':>8}{'Asks':>8}{'Directorate':>13}{'Fair':>8}")
    for lvl in status["levels"]:
        n = lvl["name"]
        d = status["modes"]["directorate"]["allocation_mw"][n]
        f = status["modes"]["fair"]["allocation_mw"][n]
        print(f"{n:<6}{lvl['population']:>8}{lvl['need_mw']:>8.1f}{lvl['request_mw']:>8.1f}{d:>13.1f}{f:>8.1f}")
    for mode in ("directorate", "fair"):
        s = status["modes"][mode]
        print(f"\n{mode.title():<12} upper levels get {s['share_to_upper_pct']}%, "
              f"{VIEWER_LEVEL} gets {s['share_to_viewer_pct']}%, "
              f"people at risk: {s['people_at_risk']:,}")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
