# -*- coding: utf-8 -*-
"""V0.6 structural alignment (the pattern-learning signal; spec 11-E/I/J,
14, 45).

Given an escalated query's numbers and the LLM's numeric answer, search
for a UNIQUE assignment of numbers to typed kinds such that a known
capability structure deterministically reproduces the answer. Only then
does the observation become pattern evidence.

Why this is pollution-resistant BY CONSTRUCTION: a wrong LLM answer is
accepted only if it coincidentally equals the exact value of a valid
typed derivation over the query's own numbers (rel tol 0.5%) — for
arithmetic errors this almost never happens, so wrong answers simply
produce NO alignment instead of wrong evidence. The LLM proposes; the
deterministic executor decides. (Measured in the E5 pollution study.)

Marker classes constrain the search and break commutative symmetry:
  currency-marked numbers -> money-family kinds only
  percent-marked          -> rate kinds only
  bare                    -> count/time/geometry/physical kinds only
"""
import itertools
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4 import registry_v4 as R4          # noqa: E402
from v3.ir import Quantity                # noqa: E402

MONEY_KINDS = ["price_per_unit", "unit_cost", "fixed_cost", "principal",
               "revenue", "cost_total", "money", "price_per_kg",
               "price_per_liter", "price_per_kwh"]
RATE_KINDS = ["rate", "rate_tax", "rate_discount"]
BARE_KINDS = ["count", "years", "length", "width", "height", "volume",
              "area", "density", "coverage_rate", "voltage", "current",
              "time", "mass", "speed", "distance"]

REL_TOL = 0.005
MAX_NUMBERS = 6


def _closure_values(assign, registry):
    """Forward closure over the registry from the assigned quantities;
    returns {kind: (value, path_tuple)} for everything derivable."""
    have = {}
    for kind, val in assign.items():
        have[kind] = (val, ())
    changed = True
    guard = 0
    while changed and guard < 60:
        changed = False
        guard += 1
        for name, spec in registry.items():
            if spec.get("transfer"):
                continue
            out_k = spec["output"]
            if out_k in have:
                continue
            if all(k in have for k in spec["inputs"]):
                ins = {k: Quantity(kind=k, value=have[k][0])
                       for k in spec["inputs"]}
                v, ok, _ = R4.execute(name, ins, registry=registry)
                if ok:
                    path = tuple(sorted(set(
                        sum((have[k][1] for k in spec["inputs"]), ())
                        + (name,))))
                    have[out_k] = (v, path)
                    changed = True
    return have


def candidate_kinds(nc):
    if nc["currency"]:
        return MONEY_KINDS
    if nc["percent"]:
        return RATE_KINDS
    return BARE_KINDS


_ANS_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

# goal-kind families for the answer-unit hint. The hint only FILTERS among
# deterministically value-verified matches (never creates one), and only
# applies when exactly one family is detected in the LLM text.
_FAMILIES = {
    "money": {"revenue", "money", "cost_var", "cost_total", "profit",
              "interest", "sale_price", "final_amount", "cost_eur",
              "net_profit", "net_interest", "unit_cost", "fixed_cost",
              "principal"},
    "mass": {"mass", "weight"},
    "area": {"area"},
    "volume": {"volume"},
    "liters": {"liters"},
    "power": {"power"},
    "energy": {"energy", "energy_j"},
    "count": {"count", "count_breakeven"},
}
_UNIT_PAT = [("money", re.compile(r"\$|dollar", re.I)),
             ("mass", re.compile(r"\bkg\b|kilogram", re.I)),
             ("area", re.compile(r"m²|square met", re.I)),
             ("volume", re.compile(r"m³|cubic met", re.I)),
             ("liters", re.compile(r"\bliters?\b|\blitres?\b", re.I)),
             ("power", re.compile(r"\bwatts?\b|\bW\b")),
             ("energy", re.compile(r"\bjoules?\b|\bJ\b")),
             ("count", re.compile(r"\bunits\b", re.I))]


def answer_unit_hint(llm_text):
    fams = {f for f, p in _UNIT_PAT if p.search(llm_text or "")}
    return fams.pop() if len(fams) == 1 else None


def answer_values(llm_text):
    """Candidate numeric answers from LLM text (last first)."""
    vals = []
    for m in _ANS_NUM.findall(llm_text or ""):
        try:
            vals.append(float(m.replace(",", "")))
        except ValueError:
            continue
    seen, out = set(), []
    for v in reversed(vals):          # last number first (V0.4 convention)
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out[:4]


def _kind_closure(kinds, reg):
    have = set(kinds)
    changed = True
    while changed:
        changed = False
        for spec in reg.values():
            if spec.get("transfer"):
                continue
            if spec["output"] not in have and \
                    all(k in have for k in spec["inputs"]):
                have.add(spec["output"])
                changed = True
    return have


# canonical preference used ONLY to merge VALUE-EQUIVALENT matches (same
# used numbers, same value, goal kinds within the asked money group) —
# a deterministic, documented tie-break, recorded on the match
_KIND_PREF = ["price_per_unit", "count", "unit_cost", "principal",
              "fixed_cost", "revenue", "cost_total", "volume", "density",
              "years", "rate", "price_per_kg", "price_per_liter",
              "price_per_kwh", "money", "mass", "area", "length",
              "width", "height", "coverage_rate", "voltage", "current",
              "time", "speed", "distance"]
_GOAL_PREF = ["revenue", "profit", "mass", "area", "volume", "interest",
              "final_amount", "cost_var", "cost_total", "money",
              "count_breakeven", "power", "energy", "liters"]


def _pref(seq, order):
    idx = {k: i for i, k in enumerate(order)}
    return sorted(seq, key=lambda m: idx.get(m, len(order)))


def align(ncs, llm_text, registry=None, max_assignments=8000,
          r1_kinds=None):
    """ncs: number_contexts() output. r1_kinds: optional list (same
    length) of SPECIFIC kinds the base parser already established for
    each number (None where unbound/generic) — used as hard constraints,
    which resolves commutative-role symmetry the surface vocabulary
    already disambiguates.

    Returns {"unique", "matches", ...}; matches differing only in
    unused numbers are identical; value-equivalent money-group matches
    (same used numbers, same value) are MERGED under the canonical
    preference and marked merged_ambiguity=k."""
    reg = registry if registry is not None else R4.REGISTRY
    if not ncs or len(ncs) > MAX_NUMBERS:
        return {"unique": False, "matches": [], "n_assignments": 0}
    answers = answer_values(llm_text)
    if not answers:
        return {"unique": False, "matches": [], "n_assignments": 0}
    # R1 constraints are hard ONLY for kinds bound to exactly one number;
    # a kind the base parser assigned twice is ambiguous surface evidence
    # and falls back to the marker class (else the distinct-kind rule
    # would make every assignment impossible)
    from collections import Counter as _C
    k1_counts = _C(k for k in (r1_kinds or []) if k)
    cand = []
    for i, nc in enumerate(ncs):
        k1 = r1_kinds[i] if r1_kinds else None
        if k1 and k1 not in ("money", "distance") and k1_counts[k1] == 1:
            cand.append([k1])           # hard constraint from base parser
        elif k1 and (k1 == "money" or k1_counts.get(k1, 0) > 1
                     ) and nc["currency"]:
            cand.append(MONEY_KINDS)
        else:
            cand.append(candidate_kinds(nc))
    # ONLY the LAST number in the LLM text is treated as the answer.
    # Earlier numbers are restated inputs or intermediates — and the
    # V0.4-measured failure mode (correct method, wrong final
    # arithmetic) leaves CORRECT intermediates in the text: falling back
    # to them would align a wrong answer's intermediate and mis-teach
    # the ask pattern (e.g. a profit question credited to 'revenue').
    # Trading recall for pollution safety here is deliberate.
    matches = {}
    n_tried = 0
    for A in answers[:1]:
        for combo in itertools.product(*cand):
            if len(set(combo)) != len(combo):
                continue                # kinds must be distinct
            n_tried += 1
            if n_tried > max_assignments:
                break
            assign = {k: ncs[i]["value"] for i, k in enumerate(combo)}
            # types-only pre-filter: if nothing new is derivable, skip
            if _kind_closure(set(assign), reg) == set(assign):
                continue
            have = _closure_values(assign, reg)
            for kind, (v, path) in have.items():
                if kind in assign and not path:
                    continue            # trivial: the number itself
                if abs(v - A) <= REL_TOL * max(abs(A), 1e-9):
                    used = {k for cap in path
                            for k in reg[cap]["inputs"] if k in assign}
                    if len(used) < 2:
                        continue
                    ident = (kind, tuple(sorted(
                        (k, assign[k]) for k in used)))
                    if ident not in matches:
                        matches[ident] = {
                            "assignment": list(combo),
                            "used": [c in used for c in combo],
                            "goal_kind": kind, "value": v,
                            "path": list(path), "answer_used": A}
                    break
        if matches or n_tried > max_assignments:
            break
    out = list(matches.values())
    # answer-unit hint: filter among verified matches only
    hint = answer_unit_hint(llm_text)
    if hint and len(out) > 1:
        filt = [m for m in out if m["goal_kind"] in _FAMILIES[hint]]
        if filt:
            out = filt
    # value-equivalent merge: same used-number VALUES, same result value,
    # all goals in the money family (the graded answer is identical) ->
    # one canonical match
    if len(out) > 1:
        used_vals = {tuple(sorted(
            ncs[i]["value"] for i, u in enumerate(m["used"]) if u))
            for m in out}
        vals = {round(m["value"], 6) for m in out}
        goals = {m["goal_kind"] for m in out}
        if len(used_vals) == 1 and len(vals) == 1 and \
                goals <= _FAMILIES["money"] | {"cost_var"}:
            k = len(out)
            best_goal = _pref(goals, _GOAL_PREF)[0]
            cands2 = [m for m in out if m["goal_kind"] == best_goal]
            cands2.sort(key=lambda m: [
                _KIND_PREF.index(x) if x in _KIND_PREF else 99
                for x in m["assignment"]])
            merged = dict(cands2[0])
            merged["merged_ambiguity"] = k
            out = [merged]
    return {"unique": len(out) == 1, "matches": out,
            "n_assignments": n_tried, "unit_hint": hint}
