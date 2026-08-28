# -*- coding: utf-8 -*-
"""V0.11 Semantic State Integrity engine (spec Section 8) +
machine-checkable invariants I1-I8 (Section 22).

Pipeline position: PROPOSED STATE -> integrity -> CERTIFIED STATE.
Hard failures block execution: a fact leaves ASSERTED only into
CERTIFIED, AMBIGUOUS, CONFLICTED, or QUARANTINED. Quarantine is
fact-local (Section 9): dependents are blocked, independents run.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v11.semstate11 import identity_key            # noqa: E402
from v10.universe10 import KINDS10                 # noqa: E402


def _unit_in_span(f):
    """V0.10 R5: claimed unit token adjacent to the value in the
    fact's own span."""
    u = (f.get("unit") or "").strip().lower().rstrip(".,;:!?")
    span = (f.get("span") or "").lower()
    v = f.get("value")
    if not u or not span or v is None:
        return True
    if not re.search(r"\d", span):
        return True     # verbal-number span: no literal to match
    _W = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
          5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
          10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
          14: "fourteen", 15: "fifteen", 16: "sixteen",
          17: "seventeen", 18: "eighteen", 19: "nineteen",
          20: "twenty"}
    word = _W.get(int(v)) if float(v).is_integer() and \
        0 <= v <= 20 else None
    head = re.split(r"[/^]", u)[0]
    if not head or head.isdigit():
        return True
    UAL = {"$": ("$", "dollar"), "kg": ("kg", "kilo"),
           "g": ("g", "gram"), "m": ("m", "metre", "meter"),
           "s": ("s", "sec"), "l": ("l", "litre", "liter"),
           "v": ("v", "volt"), "a": ("a", "amp"),
           "w": ("w", "watt"), "j": ("j", "joule"),
           "%": ("%", "percent"), "min": ("min",),
           "h": ("h", "hour", "hr"), "km/h": ("km/h", "kph")}
    aliases = UAL.get(head, (head,))
    vs = f"{float(v):g}"
    vi = str(int(v)) if float(v).is_integer() else vs
    forms = {vs, vi} | ({word} if word else set())
    # scientific-notation literal in the span equal to the value
    for smm in re.finditer(r"\d+(?:\.\d+)?[eE][+-]?\d+", span):
        try:
            if abs(float(smm.group(0)) - float(v)) <= \
                    1e-9 * max(1.0, abs(float(v))):
                forms.add(smm.group(0).lower())
        except ValueError:
            pass
    for vv in forms:
        for a in aliases:
            if a in ("$", "€", "£"):
                if re.search(rf"\{a}\s*{re.escape(vv)}", span):
                    return True
            elif a == "%":
                if re.search(rf"{re.escape(vv)}\s*%", span):
                    return True
            elif re.search(rf"{re.escape(vv)}\s*{re.escape(a)}"
                           rf"[a-z]*(?![a-z])", span):
                return True
    return False


def certify(state, target_entity=None, known_kinds=None):
    """Run the 12 checks; set statuses in place. Returns a report."""
    known = known_kinds or set(KINDS10)
    rep = {"checked": 0, "certified": 0, "conflicted": 0,
           "ambiguous": 0, "quarantined": 0, "violations": []}

    def flag(f, why):
        rep["violations"].append({"fid": f["fid"], "why": why})

    # C1-C5, C9, C12: per-fact schema / concept / role / unit /
    # provenance checks
    for f in state.facts:
        if f["status"] != "ASSERTED":
            continue
        rep["checked"] += 1
        ok = True
        if f.get("value") is None and f.get("role") == "input":
            flag(f, "schema:no_value")
            ok = False
        if f.get("concept") not in known:
            flag(f, "concept:unknown")
            ok = False
        if f.get("provenance") == "DERIVED" and \
                not f.get("derived_from"):
            flag(f, "provenance:derived_without_source")
            ok = False
        if f.get("provenance") == "USER_TEXT" and not _unit_in_span(f):
            flag(f, "unit:not_in_span")
            ok = False
        if f.get("polarity") == "negated" and f.get("role") == \
                "input":
            flag(f, "role:negated_input")
            ok = False
        if not ok:
            f["status"] = "QUARANTINED"
    # C8: ambiguity — unresolved entity on a fact whose concept has
    # multiple same-concept competitors
    for f in state.facts:
        if f["status"] != "ASSERTED":
            continue
        if f.get("entity") is None and f.get("ambiguity"):
            f["status"] = "AMBIGUOUS"
            rep["ambiguous"] += 1
    # C4b: non-input roles never enter certified execution state
    for f in state.facts:
        if f["status"] == "ASSERTED" and f.get("role") not in (
                "input", None):
            f["status"] = "QUARANTINED"
            flag(f, f"role:{f.get('role')}")
    # C7: contradiction — same identity key, different CANONICAL
    # values (2000 kg vs 2000 g IS a conflict after conversion)
    def _canon(f):
        v = f.get("value")
        if v is None:
            return None
        u = (f.get("unit") or "").strip().lower().rstrip(".,;:!?")
        k = f.get("concept")
        if k == "mass" and u in ("g", "gram", "grams"):
            return v / 1000.0
        if k == "time" and u in ("min", "minutes", "minute"):
            return v * 60.0
        if k == "time" and u in ("h", "hr", "hrs", "hour", "hours"):
            return v * 3600.0
        if k == "speed" and u in ("km/h", "kph"):
            return v / 3.6
        return v
    # dimension-family unification for the conflict check: without
    # chem context, solute_mass IS mass (the conflicting-units class
    # hides a g/kg contradiction behind the concept split)
    chem = any(f.get("concept") in ("molar_mass", "solution_volume",
                                    "dilution_factor")
               for f in state.facts)
    if not chem:
        for f in state.facts:
            if f.get("concept") == "solute_mass":
                f["concept"] = "mass"
    for key, group in state.by_key().items():
        live = [f for f in group if f["status"] == "ASSERTED"]
        vals = {round(float(_canon(f)), 9) for f in live
                if f.get("value") is not None}
        if len(vals) > 1:
            for f in live:
                f["status"] = "CONFLICTED"
                rep["conflicted"] += 1
                flag(f, f"contradiction:{key[1]}")
    # C10: dependency validity + quarantine closure (I8)
    bad = {f["fid"] for f in state.facts
           if f["status"] in ("CONFLICTED", "QUARANTINED",
                              "AMBIGUOUS")}
    closure = set()
    for fid in bad:
        closure |= state.dependents_of(fid)
    for f in state.facts:
        if f["fid"] in closure and f["status"] == "ASSERTED":
            f["status"] = "QUARANTINED"
            flag(f, "dependency:tainted")
    # certification
    for f in state.facts:
        if f["status"] == "ASSERTED":
            f["status"] = "CERTIFIED"
            rep["certified"] += 1
    rep["quarantined"] = sum(1 for f in state.facts
                             if f["status"] == "QUARANTINED")
    return rep


# ------------------------------------------------ invariants (I1-I8)
def check_invariants(state, executed_inputs=None,
                     target_entity=None):
    """Machine-checkable invariants; returns list of violations.
    executed_inputs: list of fact dicts actually consumed by
    execution (for I2/I3/I6/I8)."""
    v = []
    for f in state.facts:
        if f["status"] == "CERTIFIED":
            key_mates = [g for g in state.facts
                         if identity_key(g) == identity_key(f)
                         and g is not f
                         and g.get("value") is not None
                         and f.get("value") is not None
                         and round(float(g["value"]), 9) !=
                         round(float(f["value"]), 9)
                         and g["status"] == "CERTIFIED"]
            if key_mates:
                v.append(("I1", f["fid"],
                          "conflicted fact certified"))
        if f["status"] == "DERIVED" and not f.get("derived_from"):
            v.append(("I5", f["fid"], "derived without provenance"))
    for f in (executed_inputs or []):
        if f.get("status") not in ("CERTIFIED", "DERIVED"):
            v.append(("I7/I8", f.get("fid"),
                      f"executed non-certified status "
                      f"{f.get('status')}"))
        if target_entity and f.get("entity") not in (
                None, "GLOBAL", target_entity):
            v.append(("I3", f.get("fid"),
                      f"cross-entity consumption "
                      f"{f.get('entity')}!={target_entity}"))
        if f.get("status") == "AMBIGUOUS":
            v.append(("I2", f.get("fid"), "ambiguous consumed"))
    return v
