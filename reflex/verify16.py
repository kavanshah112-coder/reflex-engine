# -*- coding: utf-8 -*-
# origin: new for V1.6 -- post-hoc verifier on the escalated share (SPEC 4)
"""Deterministic checks over (question, LLM answer): each names a way
an answer can be IMPOSSIBLE, never a way it is merely unlikely.

Battery = the two checks proven in the draft-v1 evidence run (8/74
errors at zero false flags on 527 correct answers) plus the six
candidates, ALL subject to the frozen admission rule (SPEC 4): a check
is admitted only if it fires zero times on correct answers in dev, is
re-measured sealed, and a single sealed false flag voids it. Nothing
in this module knows what the LLM answered elsewhere or what the gold
is -- checks see the question text and one answer.

verdict(question, answer) -> {"flags": [names...], "features": {...}}
The caller decides what a flag means (retry, in the product framing).

POSITIVE CONTROL: control_battery() -- for every check, a case that
MUST fire and a paired sound case that MUST NOT. Run before any
counting run (B24).
"""
import re

_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

COUNT_ASK = re.compile(
    r"\bhow (?:many|much)\b|\bnumber of\b|\bcount\b", re.I)
DISCRETE_ASK = re.compile(
    r"\bhow many\b|\bnumber of\b", re.I)
REMAIN_ASK = re.compile(
    r"\b(left|remain|remaining|leftover|still hav|left over)\b", re.I)
GCD_SUP = re.compile(r"\b(greatest|largest|biggest)\b", re.I)
GCD_DIV = re.compile(
    r"\b(divid\w*|split|shar\w*|group\w*|"
    r"equal (?:piles|groups|rows|sets)|"
    r"(?:none|no \w{0,12}) left over)\b", re.I)

_UNIT_FAMILIES = {
    "time": {"second", "seconds", "minute", "minutes", "hour", "hours",
             "day", "days", "week", "weeks", "month", "months",
             "year", "years"},
    "money": {"dollar", "dollars", "cent", "cents", "$"},
    "length": {"meter", "meters", "metre", "metres", "km",
               "kilometer", "kilometers", "cm", "mile", "miles",
               "inch", "inches", "foot", "feet"},
    "mass": {"kg", "kilogram", "kilograms", "gram", "grams", "pound",
             "pounds", "ounce", "ounces"},
}


def _answer_value(answer):
    """First number in the answer, or None."""
    if isinstance(answer, (int, float)):
        return float(answer)
    m = _NUM.search(str(answer).replace(",", ""))
    return float(m.group(0)) if m else None


def _question_numbers(q):
    return [float(x.replace(",", ""))
            for x in _NUM.findall(q.replace(",", ""))]


def _unit_words(text):
    words = set(re.findall(r"[a-z$]+", text.lower()))
    fams = set()
    for fam, ws in _UNIT_FAMILIES.items():
        if words & ws:
            fams.add(fam)
    return fams


# ------------------------------------------------------------- checks
def chk_non_integer_count(q, answer):
    """PROVEN (5/5/0). A discrete 'how many' answered fractionally."""
    if not DISCRETE_ASK.search(q):
        return False
    v = _answer_value(answer)
    return v is not None and abs(v - round(v)) > 1e-6


def chk_negative(q, answer):
    """PROVEN (3/3/0). A count/amount below zero."""
    if not COUNT_ASK.search(q):
        return False
    v = _answer_value(answer)
    return v is not None and v < 0


def chk_not_in_text(q, answer):
    """CANDIDATE. An 'echo': the answer verbatim restates one of the
    question's own numbers although the ask requires combining at
    least two of them (kept narrow: fires only when the question
    carries 3+ numbers and asks a remainder/total)."""
    v = _answer_value(answer)
    if v is None:
        return False
    nums = _question_numbers(q)
    if len(nums) < 3:
        return False
    if not (REMAIN_ASK.search(q) or re.search(
            r"\b(in all|altogether|total)\b", q, re.I)):
        return False
    return any(abs(v - n) < 1e-9 for n in nums)


_ALL_UNITS = set().union(*_UNIT_FAMILIES.values())


def _unit_terms(text):
    return {w for w in re.findall(r"[a-z$]+", text.lower())
            if w in _ALL_UNITS}


def _norm_unit(w):
    return w.rstrip("s") if w.endswith("s") and w != "s" else w


def chk_unit_mismatch(q, answer):
    """CANDIDATE. The ask names a unit ('in hours') and the answer
    names a DIFFERENT unit word ('90 minutes') -- word-level, since a
    family-level view cannot see minutes vs hours."""
    if not isinstance(answer, str):
        return False
    m = re.search(r"\bin\s+([a-z]+)\s*\??\s*$", q.lower())
    if not m or m.group(1) not in _ALL_UNITS:
        return False
    asked = {_norm_unit(m.group(1))}
    named = {_norm_unit(w) for w in _unit_terms(answer)}
    return bool(named) and not (named & asked)


def chk_conflict_present(q, answer):
    """CANDIDATE. The question asserts two different values for the
    same quantity in two clauses and the answer uses either one
    (narrow: 'X is A. ... X is B.' with A != B)."""
    pairs = re.findall(
        r"\b(\w+ \w+|\w+)\s+(?:is|was|has|had)\s+(-?\d[\d,]*)",
        q.lower())
    seen = {}
    for name, val in pairs:
        val = float(val.replace(",", ""))
        if name in seen and abs(seen[name] - val) > 1e-9:
            v = _answer_value(answer)
            return v is not None
        seen[name] = val
    return False


def chk_superlative_arithmetic(q, answer):
    """CANDIDATE. GCD-shaped ask; a divisor of both cannot exceed the
    smaller input."""
    if not (GCD_SUP.search(q) and GCD_DIV.search(q)):
        return False
    v = _answer_value(answer)
    nums = [n for n in _question_numbers(q) if n > 0]
    if v is None or len(nums) < 2:
        return False
    return v > min(nums)


def chk_exceeds_total(q, answer):
    """CANDIDATE. A remainder cannot exceed the largest quantity in
    the question."""
    if not REMAIN_ASK.search(q):
        return False
    v = _answer_value(answer)
    nums = _question_numbers(q)
    if v is None or not nums:
        return False
    return v > max(nums) + 1e-9


def chk_impossible_precision(q, answer):
    """CANDIDATE. Five-plus decimal places from all-integer inputs of
    an add/subtract/count ask."""
    v = _answer_value(answer)
    if v is None:
        return False
    s = str(answer)
    m = re.search(r"\d+\.(\d{5,})", s.replace(",", ""))
    if not m:
        return False
    nums = _question_numbers(q)
    if not nums or any(abs(n - round(n)) > 1e-9 for n in nums):
        return False
    return bool(COUNT_ASK.search(q))


CHECKS = [
    ("non_integer_count", chk_non_integer_count, "proven"),
    ("negative", chk_negative, "proven"),
    ("not_in_text", chk_not_in_text, "candidate"),
    ("unit_mismatch", chk_unit_mismatch, "candidate"),
    ("conflict_present", chk_conflict_present, "candidate"),
    ("superlative_arithmetic", chk_superlative_arithmetic, "candidate"),
    ("exceeds_total", chk_exceeds_total, "candidate"),
    ("impossible_precision", chk_impossible_precision, "candidate"),
]


def verdict(question, answer, admitted=None):
    """Run the battery. `admitted`: names to run (None = all)."""
    flags = []
    for name, fn, status in CHECKS:
        if admitted is not None and name not in admitted:
            continue
        try:
            if fn(question, answer):
                flags.append(name)
        except (ValueError, TypeError):
            continue           # a broken check never flags
    return {"flags": flags}


# ---------------------------------------------------- positive control
def control_battery():
    """(must-fire case, must-not-fire case) per check."""
    cases = {
        "non_integer_count": (
            ("How many apples does Tom have left?", "3.5"),
            ("How many apples does Tom have left?", "4")),
        "negative": (
            ("How many pencils remain in the box?", "-2"),
            ("How many pencils remain in the box?", "0")),
        "not_in_text": (
            ("Ann had 47 stickers, gave away 12 and bought 5 more. "
             "How many does she have left?", "47"),
            ("Ann had 47 stickers, gave away 12 and bought 5 more. "
             "How many does she have left?", "40")),
        "unit_mismatch": (
            ("How long is the trip in hours?", "90 minutes"),
            ("How long is the trip in hours?", "1.5 hours")),
        "conflict_present": (
            ("The tank is 40 liters. Later the text says the tank "
             "is 60. How much fuel fits?", "60"),
            ("The tank is 40 liters. It is half full. How much "
             "fuel is inside?", "20")),
        "superlative_arithmetic": (
            ("45 stickers and 27 cards are split into equal piles "
             "with none left over. What is the greatest number of "
             "piles?", "72"),
            ("45 stickers and 27 cards are split into equal piles "
             "with none left over. What is the greatest number of "
             "piles?", "9")),
        "exceeds_total": (
            ("A jar holds 30 sweets; 12 were eaten. How many are "
             "left?", "42"),
            ("A jar holds 30 sweets; 12 were eaten. How many are "
             "left?", "18")),
        "impossible_precision": (
            ("Tom has 3 boxes of 4 pens. How many pens in total?",
             "12.000037"),
            ("Tom has 3 boxes of 4 pens. How many pens in total?",
             "12")),
    }
    fails = []
    for name, fn, _st in CHECKS:
        must, mustnot = cases[name]
        if not fn(*must):
            fails.append(("MUST-FIRE MISSED", name, must))
        if fn(*mustnot):
            fails.append(("FALSE FIRE", name, mustnot))
    # cross-battery: no check may fire on the sound cases of others
    for name, fn, _st in CHECKS:
        for other, (must, mustnot) in cases.items():
            if fn(*mustnot):
                fails.append(("CROSS FALSE FIRE", name, other))
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = control_battery()
    print("verifier control battery:", "PASS" if ok else "FAIL",
          "(%d checks)" % len(CHECKS))
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
