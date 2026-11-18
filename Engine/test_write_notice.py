"""
Tests for write_notice.py. They use a FAKE model, so they run without Ollama.
Run from the engine folder with:  python -m pytest -v
"""

from grid_engine import build_status
from write_notice import (build_facts, numbers_in, check_notice,
                          template_notice, make_notice)

STATUS = build_status()
FACTS = build_facts(STATUS)


def test_numbers_in_handles_commas_and_decimals():
    assert numbers_in("12,677 people, 3.0 MW, L40") == ["12677", "3.0", "40"]


def test_template_passes_its_own_checker():
    ok, reason = check_notice(template_notice(FACTS), FACTS)
    assert ok, reason


GOOD = (f"NOTICE TO LEVEL 40: L40 got {FACTS['viewer_got']} MW. "
        f"A fair split cuts risk from {FACTS['risk_now']} to {FACTS['risk_fair']}.")


def test_checker_accepts_engine_numbers():
    assert check_notice(GOOD, FACTS)[0]


def test_checker_rejects_vague_notice_missing_key_numbers():
    ok, reason = check_notice(f"NOTICE TO LEVEL 40: Supply is {FACTS['supply_mw']} MW.", FACTS)
    assert not ok and "missing" in reason


def test_tidy_joins_lines():
    from write_notice import tidy
    assert tidy("NOTICE TO LEVEL 40:\n\n  Power   is low.") == "NOTICE TO LEVEL 40: Power is low."


def test_checker_rejects_a_made_up_number():
    ok, reason = check_notice("NOTICE TO LEVEL 40: 99 people are at risk.", FACTS)
    assert not ok and "99" in reason


def test_checker_rejects_empty_and_too_long():
    assert not check_notice("   ", FACTS)[0]
    assert not check_notice("NOTICE TO LEVEL 40: " + "power " * 200, FACTS)[0]


def test_good_model_answer_is_kept_and_tidied():
    messy = GOOD.replace(": ", ":\n\n", 1)
    notice = make_notice(STATUS, generate=lambda prompt: messy)
    assert notice["source"] == "model" and notice["text"] == GOOD


def test_bad_model_answer_falls_back_to_template():
    notice = make_notice(STATUS, generate=lambda prompt: "NOTICE TO LEVEL 40: 1,000,000 people affected.")
    assert notice["source"] == "template"
    assert check_notice(notice["text"], FACTS)[0]


def test_model_down_falls_back_to_template():
    def broken(prompt):
        raise ConnectionError("Ollama not running")
    notice = make_notice(STATUS, generate=broken)
    assert notice["source"] == "template" and "unavailable" in notice["reason"]


def test_prompt_contains_the_facts():
    seen = {}
    make_notice(STATUS, generate=lambda prompt: seen.setdefault("p", prompt))
    for value in FACTS.values():
        assert value in seen["p"]
    assert "risk_now" not in seen["p"]  # facts are sentences, not variable names
