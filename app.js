/*
  app.js - reads status.json (made by engine/grid_engine.py) and
  sizes the AR cables and labels from the real numbers.

  The page shows three cables on Level 40's wall:
    "up"     power going to the upper levels (L12, L20)
    "middle" power going to the middle levels (L28, L33)
    "here"   power that stays on this level (L40)
  The Fair share button switches between the Directorate's split and the fair split.
*/

// ---------- Pure helper functions (no page needed, so we can test them) ----------

// Sort each level's power into the three cables.
function groupTotals(status, mode) {
  const alloc = status.modes[mode].allocation_mw;
  const totals = { up: 0, middle: 0, here: 0 };
  for (const level of status.levels) {
    const mw = alloc[level.name] || 0;
    if (level.name === status.viewer_level) totals.here += mw;
    else if (level.depth <= 20) totals.up += mw;  // same cutoff as UPPER_LEVEL_MAX_DEPTH in Python
    else totals.middle += mw;
  }
  return totals;
}

// Cable thickness. WHY square root: a cable's cross-section AREA grows with
// radius squared, so radius = sqrt(power) makes the AREA match the power.
// Double the power -> double the area (not double the width, which would exaggerate).
function radiusFor(mw) {
  const r = 0.02 * Math.sqrt(mw);
  return Math.max(r, 0.008); // never fully invisible, so you can still see a starved cable
}

// How long one flow dot takes to travel its cable. More power = faster flow.
function flowMsFor(mw) {
  if (mw <= 0) return 0;               // 0 means "no flow"
  return Math.round(4000 / Math.sqrt(mw));
}

function percent(part, whole) {
  return whole > 0 ? Math.round((100 * part) / whole) : 0;
}

// ---------- Page code (only runs in the browser) ----------

// Where each cable sits on the wall and how far up it runs (z = 1 is the bottom).
const CABLES = {
  up:     { x: -0.50, topZ: -2.0, label: "To upper levels" },
  middle: { x: -0.15, topZ: -0.8, label: "To L28 and L33" },
  here:   { x:  0.85, topZ:  0.0, label: "Stays on L40" },
};

let status = null;          // filled in once status.json loads
let mode = "directorate";   // or "fair"

function setCable(name, mw, supply) {
  const c = CABLES[name];
  const length = 1 - c.topZ;            // from z=1 (bottom) up to topZ
  const middleZ = (1 + c.topZ) / 2;

  const cable = document.getElementById("cable-" + name);
  cable.setAttribute("radius", radiusFor(mw));
  cable.setAttribute("height", length);
  cable.setAttribute("position", `${c.x} 0.05 ${middleZ}`);

  const dot = document.getElementById("dot-" + name);
  const ms = flowMsFor(mw);
  dot.setAttribute("visible", ms > 0);
  if (ms > 0) {
    // Dot sits ON the cable's center line and is 30% fatter than the cable,
    // so it pokes out cleanly instead of half-hiding inside it (that caused speckles).
    dot.setAttribute("radius", radiusFor(mw) * 1.3);
    // Replace the whole animation so the new speed takes effect right away.
    dot.setAttribute("animation", {
      property: "position",
      from: `${c.x} 0.05 1`,
      to: `${c.x} 0.05 ${c.topZ}`,
      dur: ms, loop: true, easing: "linear",
    });
  }

  document.getElementById("label-" + name).setAttribute(
    "value", `${c.label}: ${percent(mw, supply)}% (${mw.toFixed(1)} MW)`
  );
}

function render() {
  if (!status) return;
  const totals = groupTotals(status, mode);
  for (const name of Object.keys(CABLES)) {
    setCable(name, totals[name], status.supply_mw);
  }
  const risk = status.modes[mode].people_at_risk;
  document.getElementById("label-risk").setAttribute(
    "value", `People at risk: ${risk.toLocaleString()}`
  );
  const button = document.getElementById("mode-button");
  button.textContent = mode === "directorate" ? "Show fair share" : "Show Directorate split";
  document.getElementById("mode-name").textContent =
    mode === "directorate" ? "Directorate split" : "Fair share";
}

function showError(message) {
  document.getElementById("mode-name").textContent = message;
}

if (typeof document !== "undefined") {
  document.getElementById("mode-button").addEventListener("click", () => {
    mode = mode === "directorate" ? "fair" : "directorate";
    render();
  });

  // The ?t=... on the end stops Safari from showing an old saved copy.
  fetch("status.json?t=" + Date.now())
    .then((response) => {
      if (!response.ok) throw new Error("status.json not found");
      return response.json();
    })
    .then((data) => {
      status = data;
      // A-Frame may still be starting up; wait for the scene before drawing.
      const scene = document.querySelector("a-scene");
      if (scene.hasLoaded) render();
      else scene.addEventListener("loaded", render);
    })
    .catch(() => showError("Couldn't load grid data"));
}

// Lets Node run the tests on the helper functions (ignored by the browser).
if (typeof module !== "undefined") {
  module.exports = { groupTotals, radiusFor, flowMsFor, percent };
}
