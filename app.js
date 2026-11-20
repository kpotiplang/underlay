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
  renderSpace();
  renderWater();
  const button = document.getElementById("mode-button");
  button.textContent = mode === "directorate" ? "Show fair share" : "Show Directorate split";
  document.getElementById("mode-name").textContent =
    mode === "directorate" ? "Directorate split" : "Fair share";

  // Resident notice: written ahead of time by write_notice.py (the phone never runs the AI).
  // Shown only in Fair share mode, and only if status.json has one.
  const notice = document.getElementById("notice");
  const noticeText = status.notice ? status.notice.text : "";
  document.getElementById("notice-text").textContent = noticeText;
  notice.style.display = mode === "fair" && noticeText ? "block" : "none";
  if (mode !== "fair") stopSpeaking();  // don't keep talking after switching away
}

// ---------- Space: sealed rooms behind the wall ----------
// Sizes come from the room's floor area. WHY square root again: a square room of
// area A has sides of sqrt(A), so the outline's AREA matches the real floor area.

const ROOM_SLOTS = 3;
const ROOM_SCALE = 0.22;     // marker units per meter of room side
const ROOM_ROW_Z = 0.2;      // vertical position of the row of rooms on the wall
const ROOM_FIRST_X = -1.45;  // first room sits just left of the cables
const ROOM_GAP_X = 1.15;     // space between room centers

function roomSide(areaM2) {
  return ROOM_SCALE * Math.sqrt(Math.max(areaM2, 0));
}

function renderSpace() {
  const space = status.space;
  const rooms = space ? space.behind_plate : [];
  for (let i = 0; i < ROOM_SLOTS; i++) {
    const plane = document.getElementById("room-" + i);
    const label = document.getElementById("room-label-" + i);
    const room = rooms[i];
    if (!room) {               // fewer rooms than slots: hide the extra slots
      plane.setAttribute("visible", false);
      label.setAttribute("visible", false);
      continue;
    }
    const side = roomSide(room.area_m2);
    const x = ROOM_FIRST_X - i * ROOM_GAP_X;
    plane.setAttribute("width", side);
    plane.setAttribute("height", side);
    plane.setAttribute("position", `${x} -0.02 ${ROOM_ROW_Z}`);
    plane.setAttribute("visible", true);
    // Label sits just above the room (negative z = up the wall).
    label.setAttribute("position", `${x} 0.50 ${ROOM_ROW_Z - side / 2 - 0.12}`);
    label.setAttribute("value", `Sealed ${room.area_m2} m2, ${room.years_empty} yrs`);
    label.setAttribute("visible", true);
  }
  document.getElementById("label-space").setAttribute(
    "value", space ? `Sealed rooms could house ${space.families_housed} families` : " "
  );
}

// ---------- Water: Recycler 12 failure prediction (from engine/water.py) ----------

// Label text for each state. Kept short so it fits on one line (31 letters).
function waterLabel(water) {
  if (!water) return " ";
  if (water.state === "unsafe") return `${water.recycler}: UNSAFE NOW`;
  if (water.state === "warning") return `${water.recycler}: unsafe in ${water.days_to_limit} days`;
  return `${water.recycler}: water OK`;
}

function renderWater() {
  const water = status.water;
  const fault = document.getElementById("water-fault");
  // Failing (warning or unsafe): red and pulsing. OK or no data: plain teal, still.
  const failing = water && water.state !== "ok";
  fault.setAttribute("color", failing ? "#b0412e" : "#3f7f8c");
  fault.setAttribute("animation", "enabled", failing);
  document.getElementById("label-water").setAttribute("value", waterLabel(water));
}

// ---------- Voice: the phone reads the notice aloud ----------
// Uses the browser's built-in speech voice (Web Speech API). No AI and no internet:
// it just speaks the text that write_notice.py already wrote.

function canSpeak() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

function stopSpeaking() {
  if (canSpeak()) window.speechSynthesis.cancel();
  const button = document.getElementById("speak-button");
  if (button) button.textContent = "Read aloud";
}

function toggleSpeaking() {
  if (!canSpeak() || !status || !status.notice) return;
  // Tapping while it's talking stops it.
  if (window.speechSynthesis.speaking) {
    stopSpeaking();
    return;
  }
  const speech = new SpeechSynthesisUtterance(status.notice.text);
  speech.rate = 0.95;  // a little slower than normal, like an announcement
  speech.onend = stopSpeaking;
  window.speechSynthesis.speak(speech);
  document.getElementById("speak-button").textContent = "Stop";
}

function showError(message) {
  document.getElementById("mode-name").textContent = message;
}

if (typeof document !== "undefined") {
  // Hide the voice button on browsers that can't speak.
  const speakButton = document.getElementById("speak-button");
  if (!canSpeak()) speakButton.style.display = "none";
  speakButton.addEventListener("click", toggleSpeaking);

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
  module.exports = { groupTotals, radiusFor, flowMsFor, percent, roomSide, waterLabel };
}
