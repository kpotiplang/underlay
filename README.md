# Underlay

**Patriot HackFest Fall 2026 · Track: Best Solution for a Dystopian World · Solo project**

Underlay is a phone AR tool for residents of the Hollow. You point an iPhone at a Directorate maintenance plate on a tunnel wall, and it shows what's behind the wall: where the level's power actually goes, sealed rooms nobody is allowed to use, and a water recycler that's about to fail. One tap switches from the Directorate's power split to a fair one, and the app writes a notice residents can post or play out loud.

**Demo video:** VIDEO_LINK_HERE

**Live demo:** https://kpotiplang.github.io/underlay/ (open in Safari on an iPhone and point it at the plate in [`l40_plate.pdf`](l40_plate.pdf). It needs the plate to show anything, so the video is the quickest way to see it.)

## The problem

In the Hollow, the Directorate controls the power and the deep levels always lose. Residents can't see where the power goes, so they can't argue with it. Underlay makes the split visible and shows a fairer one, using numbers instead of rumors.

**Problems from the packet this addresses:**
- **#2 Sharing power fairly** (the core): shows the Directorate's split, computes a fair split, and shows how many people that protects.
- **#3 Keeping the deep levels livable:** deeper levels need more power per person for cooling, and the fair split accounts for that.
- **#6 Finding space:** finds sealed, empty rooms and how many crowded families they could house.
- **#4 Bad water (partly):** predicts when a recycler's water will become unsafe, from a trend in its sensor readings.

## What it shows

With today's simulated supply of 55 MW:

| | Directorate split | Fair share |
|---|---|---|
| Power to the upper levels (L12, L20) | 84% | 28% |
| Power that stays on Level 40 | 5% (3.0 MW) | 24% (13.3 MW) |
| People at risk | 12,677 | 4,027 |

Level 12 gets 30 MW under the Directorate and needs 5.

- **Sealed rooms:** 12 sealed rooms on Level 40 (198 m²) could house 29 of the 310 families currently sharing a room.
- **Water:** Recycler 12's water is getting cloudier by about 0.18 NTU a day and will cross the safe limit in about 3 days.

## How it works

```
Engine/grid_engine.py ─▶ status.json ─▶ Engine/write_notice.py (adds the notice) ─▶ status.json ─▶ index.html + app.js (iPhone)
  fair_share.py  water-filling split        local AI model, offline                                  A-Frame + AR.js
  space.py       sealed rooms                checker rejects any number                              draws cables, rooms, pipe,
  water.py       failure prediction          the engine didn't produce                               toggle, notice, read aloud
```

**The engine (Python).**
- **Fair split, water-filling** (`fair_share.py`): every level gets an equal share of what's left. A level that needs less than that keeps only what it needs, and the rest goes back into the pool. Serving the smallest needs first makes one loop give the right answer, and no level can get more without taking from a level that has less.
- **Directorate split** (`grid_engine.py`): every level gets a small minimum ration, then the rest goes top-down to whatever each level asks for. The upper levels ask for far more than they need.
- **Need:** people × 2.5 kW, plus 2% more per level of depth for cooling.
- **People at risk:** if a level gets 70% of its need, 30% of its people count as at risk. It's an estimate, not a medical prediction.
- **Sealed rooms** (`space.py`): a family needs at least 6 m², so a room houses its area ÷ 6, rounded down.
- **Water prediction** (`water.py`): a line of best fit (least squares) through 14 days of turbidity readings gives the trend, then the number of days until it crosses the limit. It rounds down so the warning comes early rather than late.

**The notice (offline AI).** `write_notice.py` asks a small language model (llama3.2:3b, running locally through Ollama with no internet) to turn the engine's numbers into a 2–3 sentence notice. The model only writes the wording. A checker pulls every number out of the notice and rejects it if any number didn't come from the engine, or if a key number is missing. If the model fails twice, or isn't running, it falls back to a plain template. The checker can't judge meaning, so a person reads the notice before it's used.

**The phone (HTML and JavaScript).** The page is hosted on GitHub Pages and uses A-Frame and AR.js to track the printed plate. `app.js` reads `status.json` and sizes everything from it: cable thickness and room size use square roots so the drawn *area* matches the real power or floor area. The phone never runs the AI. It shows text that was already written, and reads it aloud with the browser's built-in voice.

## What's real and what's simulated

- **Simulated:** the Hollow's power supply, populations, building records and sensor readings. There's no real Hollow.
- **Real:** the split rules, water-filling, the housing rule, the trend prediction, the number checker, and the AR tracking. All of the engine logic is covered by tests.

## Run it yourself

```
cd Engine
pip install pytest
python -m pytest -v          # 53 tests
python grid_engine.py        # computes everything, writes ../status.json
python write_notice.py       # needs Ollama with llama3.2:3b; falls back to a template without it
```
Run `grid_engine.py` before `write_notice.py`, since the engine rewrites `status.json`.

To see the AR, print `l40_plate.pdf` at actual size on matte paper (or show it full screen on a laptop), then open the live demo link in iPhone Safari and allow the camera.

## Files

| File | What it is |
|---|---|
| `index.html`, `app.js` | The AR page |
| `status.json` | The engine's output, which the page reads |
| `l40.patt` | The trained marker pattern for the Level 40 plate |
| `l40_plate.pdf` | The printable Level 40 maintenance plate |
| `Engine/fair_share.py` | Water-filling fair split |
| `Engine/grid_engine.py` | District model, both splits, people at risk |
| `Engine/space.py` | Sealed rooms and families housed |
| `Engine/water.py` | Recycler failure prediction |
| `Engine/write_notice.py` | Offline AI notice and number checker |
| `Engine/test_*.py` | 53 tests |

## What's next

- Connect the engine to live sensor data instead of simulated logs.
- Cover the whole Hollow: right now it's one wall on one level, so each wall would get its own plate showing its own section of the grid.
- A dashboard version for a level's control room.
- Repair steps for maintainers: tap a failing pipe to see how to fix it.

## How I built it

Solo, over the hackathon week. I tested three ideas on my own laptop and iPhone before picking this one. I used an AI coding assistant (Claude) throughout to help write and debug code. I made the product and design decisions, tested every step on real devices, and can explain how each part works.
