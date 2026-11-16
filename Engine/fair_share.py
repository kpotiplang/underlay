"""
fair_share.py - splits a limited supply of power between levels fairly.

The method is called "water-filling" (also known as max-min fairness).
Picture pouring water into containers of different heights:
  - Everyone gets an equal share of what's left.
  - A level that needs LESS than an equal share only takes what it needs.
  - Whatever it didn't take goes back into the pool for everyone else.

Example: 90 MW of power, three levels that need 10, 50 and 60 MW.
  Equal share would be 30 each. Level A only needs 10, so it takes 10.
  80 MW is left for B and C: 40 each. Both need more than 40, so both get 40.
  Result: A=10, B=40, C=40. Nobody can get more without taking from someone
  who already has less. That's what makes it "fair".
"""


def water_fill(supply, needs):
    """
    Split `supply` between levels by water-filling.

    supply: total power available (a number, 0 or more)
    needs:  dict of level name -> how much that level needs (each 0 or more)

    Returns a dict of level name -> how much power that level gets.
    No level ever gets more than it needs, and the total given out
    never goes over the supply.
    """
    # Reject bad input early with a clear message, instead of
    # quietly returning nonsense numbers later.
    if supply < 0:
        raise ValueError("supply can't be negative")
    for name, need in needs.items():
        if need < 0:
            raise ValueError(f"need for {name} can't be negative")

    allocation = {}
    remaining = supply

    # Serve the SMALLEST needs first. WHY: a small need gets fully met by
    # an equal share, and its leftover can then be passed on to the bigger
    # needs that come after it. Going in this order is what makes one
    # simple loop give the correct fair answer.
    levels_smallest_first = sorted(needs, key=lambda name: needs[name])

    levels_left = len(levels_smallest_first)
    for name in levels_smallest_first:
        equal_share = remaining / levels_left
        # Take the equal share, unless the level needs less than that.
        given = min(needs[name], equal_share)
        allocation[name] = given
        remaining -= given
        levels_left -= 1

    return allocation


def unmet_need(allocation, needs):
    """How much each level is short: need minus what it got (never below 0)."""
    return {name: max(0, needs[name] - allocation.get(name, 0)) for name in needs}
