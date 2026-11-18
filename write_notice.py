"""
write_notice.py - turns the engine's numbers into a short notice residents can post.

A local AI model (llama3.2 through Ollama, no internet needed) writes the SENTENCES.
The NUMBERS always come from the engine. A checker rejects any notice that
contains a number the engine didn't produce, and falls back to a plain template.
So the model can't slip a made-up number onto the phone.

Run AFTER grid_engine.py (it adds the notice into status.json):
    python grid_engine.py
    python write_notice.py
Ollama must be running (it starts with Windows after install; check with: ollama list).
"""

import json
import re
import urllib.request
from pathlib import Path

MODEL = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"
STATUS_PATH = Path(__file__).resolve().parent.parent / "status.json"
MAX_CHARS = 450      # a notice, not an essay
ATTEMPTS = 2         # ask the model twice before falling back to the template


def build_facts(status):
    """The only numbers the notice is allowed to use, already formatted."""
    d = status["modes"]["directorate"]
    f = status["modes"]["fair"]
    viewer = status["viewer_level"]
    need = {lvl["name"]: lvl["need_mw"] for lvl in status["levels"]}
    top = min(status["levels"], key=lambda lvl: lvl["depth"])["name"]  # most upper level

    def mw(x):
        return f"{x:.1f}"

    return {
        "supply_mw": str(status["supply_mw"]),
        "top_level": top,
        "top_got": mw(d["allocation_mw"][top]),
        "top_need": mw(need[top]),
        "viewer_level": viewer,
        "viewer_got": mw(d["allocation_mw"][viewer]),
        "viewer_need": mw(need[viewer]),
        "viewer_fair": mw(f["allocation_mw"][viewer]),
        "upper_pct_now": str(d["share_to_upper_pct"]),
        "upper_pct_fair": str(f["share_to_upper_pct"]),
        "risk_now": f"{d['people_at_risk']:,}",
        "risk_fair": f"{f['people_at_risk']:,}",
    }


def numbers_in(text):
    """Every number written in the text, with commas removed: '12,677' -> '12677'."""
    return [n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]


def allowed_numbers(facts):
    """All numbers that appear anywhere in the facts (including inside 'L40')."""
    allowed = set()
    for value in facts.values():
        allowed.update(numbers_in(value))
    return allowed


# Numbers a notice MUST include, or it's too vague to be useful on a wall.
REQUIRED_FACTS = ("viewer_got", "risk_now", "risk_fair")


def check_notice(text, facts):
    """
    Returns (ok, reason). WHY so strict: a wrong number on the wall is worse
    than a plain template, because residents would act on it.
    """
    if not text or not text.strip():
        return False, "empty"
    if len(text) > MAX_CHARS:
        return False, "too long"
    allowed = allowed_numbers(facts)
    for n in numbers_in(text):
        if n not in allowed:
            return False, f"number not from the engine: {n}"
    for key in REQUIRED_FACTS:
        if facts[key] not in text:
            return False, f"missing key number: {facts[key]}"
    return True, "ok"


def tidy(text):
    """Collapse line breaks and extra spaces into one clean paragraph."""
    return " ".join(text.split())


def template_notice(facts):
    """Plain fallback. Uses only the facts, so it always passes the checker."""
    return (f"NOTICE TO LEVEL {facts['viewer_level'][1:]}: Today {facts['top_level']} received "
            f"{facts['top_got']} MW against a need of {facts['top_need']} MW, while "
            f"{facts['viewer_level']} received {facts['viewer_got']} MW of the "
            f"{facts['viewer_need']} MW it needs. A need-based split gives "
            f"{facts['viewer_level']} {facts['viewer_fair']} MW and cuts people at risk "
            f"from {facts['risk_now']} to {facts['risk_fair']}.")


def build_prompt(facts):
    """
    The facts go in as plain sentences (small models understand meaning better
    than variable names), plus one example notice to copy the style from.
    The example uses made-up levels and numbers on purpose, so the model has to
    use the real facts instead of copying the example's numbers.
    """
    lvl = facts["viewer_level"]
    sentences = (
        f"- Today's geothermal supply is {facts['supply_mw']} MW.\n"
        f"- Under the Directorate's split, {facts['top_level']} received {facts['top_got']} MW "
        f"but needs only {facts['top_need']} MW.\n"
        f"- Under the Directorate's split, {lvl} received {facts['viewer_got']} MW "
        f"but needs {facts['viewer_need']} MW.\n"
        f"- The upper levels get {facts['upper_pct_now']}% of all power now, "
        f"and would get {facts['upper_pct_fair']}% under a need-based split.\n"
        f"- A need-based split would give {lvl} {facts['viewer_fair']} MW.\n"
        f"- People at risk: {facts['risk_now']} now, {facts['risk_fair']} under a need-based split.\n"
    )
    # Wording note: every level in the example is described as "got X MW but needs Y MW".
    # An earlier example said "got X of the Y MW it needs", and the model copied that phrase
    # onto the upper level, which made it sound short when it really had too much.
    example = ("NOTICE TO LEVEL 9: The Directorate gave L2 24.0 MW, but L2 needs only 6.0 MW. "
               "L9 got 2.0 MW, but L9 needs 11.5 MW. Splitting power by need would "
               "cut people at risk from 8,410 to 2,950. Take this to your section officer.")
    return (
        f"You write short public notices for residents of {lvl} in an underground city. "
        "The Directorate is the government that controls the power.\n"
        f"Write ONE notice of 2 or 3 plain sentences. Start with: NOTICE TO LEVEL {lvl[1:]}:\n"
        "Say who is getting too much power, what this level gets, and how a need-based split "
        "would change the number of people at risk. Use ONLY the numbers in the facts, "
        "written exactly as given. No greetings, no lists, no exclamation marks.\n\n"
        f"Facts:\n{sentences}\n"
        f"Example of the style (different level, different numbers - do NOT reuse them):\n{example}\n\n"
        "Notice:"
    )


def ask_ollama(prompt):
    """Send the prompt to the local model and return its text. Raises on any failure."""
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,                      # one full answer, not word by word
        "options": {"temperature": 0.2},      # low = steadier wording, fewer surprises
    }).encode()
    request = urllib.request.Request(OLLAMA_URL, data=body,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())["response"].strip()


def make_notice(status, generate=ask_ollama):
    """
    Try the model; keep its notice only if the checker passes. Otherwise use the template.
    `generate` is a parameter so tests can pass a fake model instead of Ollama.
    Returns a dict: {"text", "source", "reason"}.
    """
    facts = build_facts(status)
    reason = "not tried"
    for _ in range(ATTEMPTS):
        try:
            text = tidy(generate(build_prompt(facts)))
        except Exception as error:            # Ollama not running, timeout, bad reply...
            reason = f"model unavailable: {error.__class__.__name__}"
            break                              # no point retrying a dead connection
        ok, reason = check_notice(text, facts)
        if ok:
            return {"text": text, "source": "model", "reason": "ok"}
    return {"text": template_notice(facts), "source": "template", "reason": reason}


def main():
    status = json.loads(STATUS_PATH.read_text())
    notice = make_notice(status)
    status["notice"] = notice
    STATUS_PATH.write_text(json.dumps(status, indent=2))
    print(notice["text"])
    print(f"\n(source: {notice['source']}; checker: {notice['reason']})")
    print(f"Saved into {STATUS_PATH}")


if __name__ == "__main__":
    main()
