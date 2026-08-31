# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W4 capability applicability (V1_4_SPEC section 7)
"""A capability that is mathematically correct and semantically
inapplicable is not safe.

V1.3's finding 6, stated in the user's own words: *speed x time can be
dimensionally correct while ignoring round trips, frequency, multiple
segments, or story-specific semantics.* The arc's capabilities carry
`{expr, inputs, output}` and nothing else, so a dimensional match is
the whole admission test. `distance = speed * time` fires on a round
trip and returns half the answer with a full certificate.

This module adds preconditions **on relational state** -- not on types.
The distinction matters: a type check asks "are these the right kind of
thing", and this asks "is this the situation the capability was written
for".

THE STRICT RULE, and the reason it is strict:

    a condition must be ESTABLISHED, not merely un-contradicted.

An engine that executes whenever nothing objects is an engine whose
safety depends on the completeness of its objections. V1.3 measured
what that is worth: five wrong answers, every check passing, because
nothing in the system was looking for the thing that was wrong. So
`require` needs positive evidence, and `forbid` needs positive evidence
of ABSENCE -- which is obtainable here, because the state is a complete
finite representation of one query. Absence in a closed structure is a
fact, not an assumption.

Conditions live in `packs/v14/applicability.json`, an OVERLAY. They are
never written into `packs/physics/caps.json`: that pack feeds Tier A,
whose 0.000 wrong-fire over 10,160 traps is the baseline this version is
measured against.
"""
import json
import re
from pathlib import Path

ESTABLISHED = "established"
REFUTED = "refuted"
UNKNOWN = "unknown"

OVERLAY = (Path(__file__).resolve().parent.parent / "packs" / "v14" /
           "applicability.json")

# Hand-authored structural markers. Few, documented, and their failure
# mode is benign in the direction that matters: a marker that fires
# spuriously makes a capability abstain, which costs coverage and is
# measured by ablation C3. A marker that fails to fire returns V1.3
# behaviour -- it cannot make anything worse than the baseline.
MARKERS = {
    "return_trip": r"\b(round trip|round-trip|there and back|"
                   r"back home|returns?|returned|way back|"
                   r"same way back|and back)\b",
    "repetition": r"\b(each (day|week|month|year|time)|every "
                  r"(day|week|month|year|time)|per (day|week|month|"
                  r"year)|twice a|three times a|repeatedly|"
                  r"once a (day|week|month))\b",
    "multi_segment": r"\b(first leg|second leg|then (drove|walked|ran|"
                     r"travelled|traveled|cycled)|next (he|she|they) "
                     r"(drove|walked|ran)|another \d+ (miles|km|"
                     r"kilometers|hours))\b",
    "journey_state": r"\b(stopped|rest(ed)?|break|paused|detour|"
                     r"traffic|delayed)\b",
}

_CACHE = {}


def load_overlay(path=None):
    p = Path(path or OVERLAY)
    key = str(p)
    if key not in _CACHE:
        _CACHE[key] = (json.loads(p.read_text(encoding="utf-8"))
                       if p.exists() else {})
    return _CACHE[key]


# ------------------------------------------------------------ markers
def marker_present(state, tag):
    """Is a structural marker asserted anywhere in this state?

    Evaluated over spans, which are verbatim source text, so a positive
    is evidence from the query rather than an inference about it.
    """
    pat = MARKERS.get(tag)
    if not pat:
        return UNKNOWN, "no marker pattern for %r" % tag
    hay = " ".join(
        [(e.get("span") or "") for e in
         list(state.nodes.values()) + list(state.relations.values())]
        + [state.source]).lower()
    if re.search(pat, hay):
        return ESTABLISHED, "marker %r present" % tag
    return REFUTED, "marker %r absent from a complete state" % tag


# --------------------------------------------------------- conditions
def _c_target_relates_to(state, binding, arg):
    tgt = binding.get("target_kind")
    if not tgt:
        return UNKNOWN, "no target kind derived"
    if tgt == arg:
        return ESTABLISHED, "target kind is %s" % arg
    return REFUTED, "target kind %s != %s" % (tgt, arg)


def _c_same_segment(state, binding, args):
    segs = set()
    for name in (args or []):
        nid = binding.get(name)
        if nid is None:
            return UNKNOWN, "input %r unbound" % name
        seg = ((state.get(nid) or {}).get("context") or {}).get("segment")
        segs.add(seg)
    if len(segs) == 1 and None not in segs:
        return ESTABLISHED, "all inputs in segment %r" % segs.pop()
    if len(segs) > 1:
        return REFUTED, "inputs span segments %s" % sorted(
            str(s) for s in segs)
    # No segment recorded anywhere. That is established as a single
    # implicit segment ONLY if nothing in the query says otherwise.
    st, why = marker_present(state, "multi_segment")
    if st == REFUTED:
        return (ESTABLISHED,
                "single implicit segment (no multi-segment marker)")
    return UNKNOWN, "segments not recorded and %s" % why


def _c_segment_identified(state, binding, arg):
    any_seg = any(((n.get("context") or {}).get("segment"))
                  for n in state.nodes.values())
    if any_seg:
        return ESTABLISHED, "an explicit segment is recorded"
    st, why = marker_present(state, "multi_segment")
    if st == REFUTED:
        return ESTABLISHED, "single implicit segment"
    return UNKNOWN, why


def _c_unresolved_relation(state, binding, arg):
    """forbid: an unresolved relation of this flavour."""
    pat = MARKERS.get(arg)
    if pat:
        for r in state.relations.values():
            if re.search(pat, (r.get("span") or "").lower()) and \
                    not r.get("resolved"):
                return ESTABLISHED, "unresolved %r relation present" % arg
        st, why = marker_present(state, arg)
        if st == ESTABLISHED:
            return ESTABLISHED, "%s asserted in the query" % arg
        return REFUTED, "no %s relation in a complete state" % arg
    return (ESTABLISHED, "unresolved relations present") \
        if state.unresolved() else (REFUTED, "no unresolved relations")


def _c_conflicting_relation(state, binding, arg):
    ops = {}
    pat = MARKERS.get(arg)
    for r in state.relations.values():
        if pat and not re.search(pat, (r.get("span") or "").lower()):
            continue
        op = (r.get("resolved") or {}).get("op")
        if op:
            ops.setdefault(op, []).append(r["id"])
    if len(ops) > 1:
        return ESTABLISHED, "conflicting %s relations: %s" % (
            arg, sorted(ops))
    return REFUTED, "no conflicting %s relation" % arg


CONDITIONS = {
    "target_relates_to": _c_target_relates_to,
    "same_segment": _c_same_segment,
    "segment_identified": _c_segment_identified,
    "unresolved_relation": _c_unresolved_relation,
    "conflicting_relation": _c_conflicting_relation,
}


# -------------------------------------------------------------- check
def check(cap_name, state, binding=None, path=None):
    """-> (ok, report).

    ok requires EVERY `require` to be ESTABLISHED and EVERY `forbid` to
    be REFUTED. An UNKNOWN on either side blocks execution: not knowing
    whether a capability applies is not a licence to apply it.

    A capability with no authored conditions returns ok with
    `unconditioned: True`, preserving V1.3 behaviour so ablation C3
    measures exactly what the conditions buy and nothing else.
    """
    ov = load_overlay(path)
    spec = ov.get(cap_name)
    binding = binding or {}
    if not spec:
        return True, {"cap": cap_name, "unconditioned": True}

    rep = {"cap": cap_name, "unconditioned": False,
           "require": [], "forbid": []}
    ok = True
    for cond in spec.get("applicability", []):
        if "require" in cond:
            fn = CONDITIONS.get(cond["require"])
            if fn is None:
                ok = False
                rep["require"].append({"name": cond["require"],
                                       "status": UNKNOWN,
                                       "why": "no evaluator"})
                continue
            a = cond.get("args", cond.get("arg"))
            st, why = fn(state, binding, a)
            rep["require"].append({"name": cond["require"], "arg": a,
                                   "status": st, "why": why})
            if st != ESTABLISHED:
                ok = False
        elif "forbid" in cond:
            fn = CONDITIONS.get(cond["forbid"])
            if fn is None:
                ok = False
                rep["forbid"].append({"name": cond["forbid"],
                                      "status": UNKNOWN,
                                      "why": "no evaluator"})
                continue
            a = cond.get("args", cond.get("arg"))
            st, why = fn(state, binding, a)
            rep["forbid"].append({"name": cond["forbid"], "arg": a,
                                  "status": st, "why": why})
            if st != REFUTED:
                ok = False
    rep["ok"] = ok
    return ok, rep


def coverage(path=None):
    """How many capabilities carry conditions. Reported, not assumed:
    an overlay covering 6 of 58 capabilities buys less than one
    covering all of them, and the report must say which it is."""
    ov = load_overlay(path)
    return {"conditioned_capabilities": len(ov),
            "conditions": sum(len(v.get("applicability", []))
                              for v in ov.values())}
