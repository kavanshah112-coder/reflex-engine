# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W2 relation resolution (V1_4_SPEC section 5)
"""A relation phrase is stored as stated and resolved separately.

V1.3 had the model emit `mul(q3, q8)`. By the time the engine saw it,
the reading was already chosen and no check could recover the fact that
a choice had been made. The single wrong answer that survived every
deterministic check AND the corroborator was this:

    "After scoring 14 points, Erin now has three times more points
     than Sara, who scored 8. How many points did Erin have before?"
        served 10   (3 x 8 = 24, minus 14)
        gold   18   (8 + 3 x 8 = 32, minus 14)

Both readings of "three times more" are defensible. Opus and sonnet
produced the SAME wrong value across four independent samples, so the
misreading is model-invariant -- which is precisely why V1.3's proposed
remedy (corroborate with a different model) would not have caught it.

The remedy here is deterministic and needs no model at all: **ambiguity
is a property of the phrase.** A phrase in the frozen AMBIGUITY SET
abstains instead of resolving. That costs coverage on every problem
using such a phrase, including the ones a model would have read
correctly, and that cost is measured rather than assumed (W2 acceptance,
SPEC section 5).

Three outcomes, no fourth:

    RESOLVED    exactly one operator -> proceed
    AMBIGUOUS   in the frozen set    -> abstain
    UNKNOWN     not in the table     -> abstain, logged to the residual

UNKNOWN abstaining is deliberate. A relation vocabulary is a closed
universe, and V1.2's lesson is that closed universes close at 100% and
real language still walks through them. The residual log is how the
next version learns what is missing.
"""
import re

RESOLVED = "resolved"
AMBIGUOUS = "ambiguous"
UNKNOWN = "unknown"


class Outcome:
    def __init__(self, status, op=None, rule=None, why=""):
        self.status = status
        self.op = op
        self.rule = rule
        self.why = why

    def __repr__(self):
        return "Outcome(%s, op=%r, rule=%r)" % (self.status, self.op,
                                                self.rule)

    def as_dict(self):
        return {"status": self.status, "op": self.op,
                "rule": self.rule, "why": self.why}


def _n(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


# ---------------------------------------------------------------------
# AMBIGUITY SET -- FROZEN 2026-09-01 (SPEC section 5.1 + amendment D-v).
# May not be extended after the first sealed run.
#
# Each entry: (id, name, test, why). `test(span, ctx)` returns True when
# the phrase is genuinely ambiguous IN THIS SPAN. Entries are checked
# BEFORE the relation table, so ambiguity always wins over a resolution.
# ---------------------------------------------------------------------

def _a1(s, ctx):
    """1. "times more" / "times as many" with an implicit base.

    Reading of the frozen text, recorded so implementation and
    pre-registration are reconciled explicitly rather than silently:
    "N times MORE than X" is idiomatically ambiguous between N*X and
    (N+1)*X even when X is named -- the ambiguity is carried by "more",
    not by a missing comparand. "N times AS MANY AS X" is not
    ambiguous when X is present, and is ambiguous when it is not.
    """
    if re.search(r"\btimes\s+(more|greater|larger|bigger|higher)\b", s):
        return True
    if re.search(r"\btimes\s+as\s+(many|much)\b", s):
        return not re.search(r"\btimes\s+as\s+(many|much)\s+\w*\s*as\b", s)
    return False


def _a2(s, ctx):
    """2. "as much again" -- adds one base or states one base."""
    return bool(re.search(r"\bas\s+(much|many)\s+again\b", s))


def _a3(s, ctx):
    """3. "half again as many"."""
    return bool(re.search(r"\bhalf\s+again\b", s))


def _a4(s, ctx):
    """4. "more than X" where X is itself derived, not given."""
    if not re.search(r"\b(more|less|fewer)\s+than\b", s):
        return False
    return bool((ctx or {}).get("comparand_is_derived"))


def _a5(s, ctx):
    """5. bare "the other" / "the rest" with >1 candidate antecedent."""
    if not re.search(r"\bthe\s+(other|rest|remainder)\b", s):
        return False
    return int((ctx or {}).get("candidate_antecedents", 0)) > 1


def _a6(s, ctx):
    """6. "average" with no stated population."""
    if not re.search(r"\b(average|mean)\b", s):
        return False
    return not (ctx or {}).get("population_stated")


def _a7(s, ctx):
    """7. "each" where the distributee is ambiguous between entities."""
    if not re.search(r"\beach\b", s):
        return False
    return int((ctx or {}).get("candidate_distributees", 0)) > 1


def _a8(s, ctx):
    """8. percentage with no stated base. V1.3 refusal class: the 100
    is never in the text, so any plan must invent it."""
    if not re.search(r"%|\bpercent\b", s):
        return False
    return not (ctx or {}).get("percent_base_stated")


def _a9(s, ctx):
    """9. bare multiplier with implicit base. V1.3 extracted "half" as
    0.5 where the plan needed 2 -- the word denotes a ratio and an
    operation, and the span does not say which."""
    return bool(re.search(
        r"\b(half|twice|double|doubled|triple|tripled|quadruple)\b", s)
        and not (ctx or {}).get("multiplier_base_stated"))


def _a10(s, ctx):
    """10. "remaining"/"left" after >=2 depletion events, no anchor."""
    if not re.search(r"\b(remain|remaining|left|leftover)\b", s):
        return False
    return int((ctx or {}).get("depletion_events", 0)) >= 2


def _a11(s, ctx):
    """11. "between X and Y" -- inclusive vs exclusive."""
    return bool(re.search(r"\bbetween\b.+\band\b", s))


def _a12(s, ctx):
    """12. a BOUND stated where a VALUE is expected."""
    return bool(re.search(
        r"\b(up to|at least|at most|no more than|no fewer than|"
        r"minimum of|maximum of)\b", s))


def _a13(s, ctx):
    """13. comparative against an unstated population."""
    return bool(re.search(
        r"\b(above|below)\s+average\b|\bthan\s+(usual|normal|typical)\b",
        s))


def _a14(s, ctx):
    """14. "per"/"a piece"/"each" with an ambiguous distributee."""
    if not re.search(r"\bper\b|\ba\s+piece\b|\beach\b|\bapiece\b", s):
        return False
    return int((ctx or {}).get("candidate_distributees", 0)) > 1


AMBIGUITY_SET = [
    (1, "times_more_implicit_base", _a1,
     "N times more is idiomatically N* or (N+1)*"),
    (2, "as_much_again", _a2, "adds one base, or states one base"),
    (3, "half_again", _a3, "1.5x or 0.5x depending on reading"),
    (4, "more_than_derived", _a4, "comparand is itself derived"),
    (5, "the_other_multi", _a5, "more than one candidate antecedent"),
    (6, "average_no_population", _a6, "population not stated"),
    (7, "each_multi_distributee", _a7, "distributee ambiguous"),
    (8, "percent_no_base", _a8, "percentage base absent from text"),
    (9, "bare_multiplier", _a9, "half/twice/double: ratio or operation"),
    (10, "remaining_multi_depletion", _a10,
     "which remainder is asked for"),
    (11, "between_bounds", _a11, "inclusive vs exclusive"),
    (12, "bound_not_value", _a12, "a bound stated where a value is due"),
    (13, "comparative_no_population", _a13, "population unstated"),
    (14, "per_multi_distributee", _a14, "distributee ambiguous"),
]

# ---------------------------------------------------------------------
# RELATION TABLE. Ordered; first match wins. Deliberately conservative:
# a phrase that is not clearly one operator belongs in UNKNOWN, where it
# abstains and gets logged, rather than being forced into the nearest
# operator. Coverage lost this way is recoverable in a later version;
# a wrong answer served is not.
# ---------------------------------------------------------------------
RELATION_TABLE = [
    ("accumulate", r"\b(bought|got|gained|found|received|added|earned|"
                   r"collected|picked up|won)\b", "add"),
    ("deplete", r"\b(left|leave|leaves|lost|gave away|gave|sold|ate|"
                r"used|spent|removed|took away|broke)\b", "sub"),
    ("total", r"\b(in all|altogether|all together|in total|combined|"
              r"total of|sum of)\b", "add"),
    ("difference", r"\b(how many more|how many fewer|how much more|"
                   r"difference between|difference in|fewer than|"
                   r"more than)\b", "sub"),
    ("rate", r"\b(per|apiece|a piece|each|every)\b", "mul"),
    ("partition", r"\b(shared equally|split equally|divided among|"
                  r"divided equally|split among|distributed equally|"
                  r"equal amount|equally)\b", "div"),
    ("scale_explicit", r"\btimes\s+as\s+(many|much)\s+\w*\s*as\b", "mul"),
]


def resolve(span, ctx=None):
    """-> Outcome. Ambiguity is checked FIRST and always wins."""
    s = _n(span)
    if not s:
        return Outcome(UNKNOWN, why="empty_span")
    for eid, name, test, why in AMBIGUITY_SET:
        try:
            if test(s, ctx):
                return Outcome(AMBIGUOUS, rule="A%d:%s" % (eid, name),
                               why=why)
        except Exception:
            continue
    for name, pat, op in RELATION_TABLE:
        if re.search(pat, s):
            return Outcome(RESOLVED, op=op, rule=name,
                           why="matched %s" % name)
    return Outcome(UNKNOWN, why="no rule matched")


def resolve_state(state, ctx_for=None):
    """Resolve every relation in an rss.State.

    Returns (all_resolved, report). The engine writes `resolved`; a
    producer never can (rss.ENGINE_ONLY).
    """
    rep = {"resolved": 0, "ambiguous": [], "unknown": []}
    for rid, r in sorted(state.relations.items()):
        ctx = ctx_for(r) if ctx_for else None
        out = resolve(r.get("span", ""), ctx)
        if out.status == RESOLVED:
            state.resolve_relation(rid, out.op, out.why)
            rep["resolved"] += 1
        elif out.status == AMBIGUOUS:
            rep["ambiguous"].append({"id": rid, "rule": out.rule,
                                     "span": r.get("span", "")[:70]})
        else:
            rep["unknown"].append({"id": rid,
                                   "span": r.get("span", "")[:70]})
    ok = not rep["ambiguous"] and not rep["unknown"]
    return ok, rep
