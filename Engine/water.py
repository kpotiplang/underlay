"""
water.py - predicts when a water recycler's output will become unsafe to drink.

A sensor reads the water's cloudiness (turbidity, in NTU) once a day. Cloudier
water means the recycler's filters are failing. We fit a straight line through
the readings to get the trend (how much cloudier per day), then work out how
many days until that line crosses the safe limit.

The readings are SIMULATED (we have no real Hollow). The math is real:
it's the same "line of best fit" (least squares) you'd do in a stats class.
"""

import math

SAFE_LIMIT_NTU = 4.0   # in our simulation, water above this is unsafe to drink
WARN_DAYS = 7          # warn if the limit will be crossed within a week
HOMES_SERVED = 340     # homes on Level 40 fed by Recycler 12

# Simulated sensor log for Recycler 12: one reading per day, oldest first.
# The trend climbs about 0.18 NTU per day, with small day-to-day noise.
RECYCLER_12_NTU = [1.02, 1.15, 1.41, 1.52, 1.70, 1.93, 2.04,
                   2.30, 2.41, 2.58, 2.83, 2.95, 3.12, 3.34]


def fit_line(values):
    """
    Line of best fit through (day 0, values[0]), (day 1, values[1]), ...
    Returns (slope, intercept): value is about slope * day + intercept.
    WHY least squares: one noisy reading can't swing the result much,
    because every reading pulls on the line a little.
    """
    n = len(values)
    if n < 2:
        raise ValueError("need at least 2 readings to see a trend")
    days = range(n)
    mean_day = sum(days) / n
    mean_value = sum(values) / n
    # slope = how days and values move together / how spread out the days are
    top = sum((d - mean_day) * (v - mean_value) for d, v in zip(days, values))
    bottom = sum((d - mean_day) ** 2 for d in days)
    slope = top / bottom
    intercept = mean_value - slope * mean_day
    return slope, intercept


def days_until_limit(values, limit=SAFE_LIMIT_NTU):
    """
    Whole days until the trend line crosses the limit.
      0     -> already unsafe (latest reading at or over the limit)
      None  -> not getting worse, so no crossing predicted
    Rounded DOWN on purpose: a warning that comes a little early is safer
    than one that comes a little late.
    """
    if values[-1] >= limit:
        return 0
    slope, intercept = fit_line(values)
    if slope <= 0:
        return None
    today = len(values) - 1
    today_on_line = slope * today + intercept
    return max(0, math.floor((limit - today_on_line) / slope))


def water_state(days):
    """Turn the prediction into one word the AR page can color by."""
    if days == 0:
        return "unsafe"
    if days is not None and days <= WARN_DAYS:
        return "warning"
    return "ok"


def build_water(values=RECYCLER_12_NTU, limit=SAFE_LIMIT_NTU):
    """Summary the AR page reads."""
    slope, _ = fit_line(values)
    days = days_until_limit(values, limit)
    return {
        "recycler": "Recycler 12",
        "latest_ntu": values[-1],
        "limit_ntu": limit,
        "trend_ntu_per_day": round(slope, 3),
        "days_to_limit": days,
        "state": water_state(days),
        "homes_served": HOMES_SERVED,
        "note": "Simulated sensor readings. The trend math is real.",
    }


if __name__ == "__main__":
    w = build_water()
    print(f"{w['recycler']}: {w['latest_ntu']} NTU now, rising {w['trend_ntu_per_day']} NTU/day, "
          f"limit {w['limit_ntu']} NTU -> unsafe in {w['days_to_limit']} days ({w['state']})")
