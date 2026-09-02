# -*- coding: utf-8 -*-
# origin: new for V1.6 -- the composed serving surface (SPEC 5)
"""ask16(): Tier A first, then the symbolic path, else escalate.

    ask16(text) -> {"status": SERVED | ESCALATED | ABSTAINED, ...}

  * Tier A (V1.0-V1.2 engine) runs UNTOUCHED and first. A pm_answer is
    served with a taxonomy address derived from evidence: the derived
    output concept, disambiguated by which capability's inputs are
    actually present in the certified state (B25: never a name alone).
  * If Tier A abstains on a coverage gap, the calculator-register
    parser (sciparse16) tries to produce a structured task; taxonomy16
    places it (op+operands only) and symcore16 executes it behind the
    independent witness gate. Refusals of any kind escalate.
  * Integrity hazards (Tier A ABSTAINED) stay ABSTAINED -- a detected
    contradiction is never handed onward silently (V1.0 rule).

No LLM adapter lives here. The escalated share is measured and, in
model arms, answered through the isolated bridge -- never in-process.
"""
import json
import re
import time
from pathlib import Path

from . import sciparse16, symcore16, taxonomy16

SERVED = "SERVED"
ESCALATED = "ESCALATED"
ABSTAINED = "ABSTAINED"

HAZARD_REASONS = {"invariant_violation", "redundancy_mismatch",
                  "target_entity_ambiguous"}

# A question that asks for a CHOICE is never answered with a quantity.
# Probe finding (2026-09-02): "Which energy is larger ..." parsed into
# facts and Tier A served a joule figure -- a number is the wrong TYPE
# of answer for a comparison ask. (V1.2 ambiguity-guard lineage.)
CHOICE_ASK = re.compile(
    r"\bwhich (?:one |of .{0,40})?(?:is|has|was)\b|"
    r"\bwhich (?:energy|value|quantity|number|option)\b", re.I)

# "... in <unit>" at the end of an ask: the engine must honor the
# requested unit or hand the query on. Probe finding: KE asked in kJ,
# served in J -- right physics, wrong answer.
_UNIT_WORDS = {
    "kilojoules": "kJ", "kilojoule": "kJ", "kj": "kJ",
    "joules": "J", "joule": "J",
    "km/h": "km/h", "kph": "km/h", "kilometers per hour": "km/h",
    "kilometres per hour": "km/h",
    "m/s": "m/s", "meters per second": "m/s",
    "metres per second": "m/s",
    "minutes": "minute", "seconds": "second", "hours": "hour",
    "grams": "g", "kilograms": "kg",
    "centimeters": "cm", "centimetres": "cm",
    "millilitres": "mL", "milliliters": "mL", "ml": "mL",
    "newtons": "N", "watts": "W", "volts": "V", "amperes": "A",
    "percent": "percent", "per cent": "percent", "percentage": "percent",
}
_REQ_UNIT = re.compile(
    r"\b(?:in|expressed in)\s+(%s)\b" % "|".join(
        re.escape(w) for w in sorted(_UNIT_WORDS, key=len,
                                     reverse=True)), re.I)

_ENGINE = None
_CAPS = None
_KINDS = None
_UREG = None


def _boot():
    global _ENGINE, _CAPS, _KINDS, _UREG
    if _ENGINE is None:
        from .engine import Engine
        _ENGINE = Engine()
        root = Path(__file__).resolve().parents[1]
        _CAPS = json.loads((root / "packs" / "physics" / "caps.json")
                           .read_text(encoding="utf-8"))
        _KINDS = json.loads((root / "packs" / "physics" / "kinds.json")
                            .read_text(encoding="utf-8"))
        try:
            import pint
            _UREG = pint.UnitRegistry()
        except Exception:
            _UREG = None
    return _ENGINE


def _more_specific_asked(text, concept):
    """True when the text contains a LONGER known concept noun that
    embeds the served concept's noun ('profit margin' asked, 'profit'
    served). Probe finding: the target namer matches the head noun and
    the dimensional gate cannot see the difference -- the gsm1120
    class. Evidence is noun tables, not the namer's opinion (B25)."""
    kn = _KINDS.get(concept) or {}
    own = [n.lower() for n in (kn.get("nouns") or [concept])]
    low = text.lower()
    for k, spec in _KINDS.items():
        if k == concept:
            continue
        for noun in (spec.get("nouns") or []):
            noun = noun.lower()
            if noun not in low:
                continue
            for o in own:
                # a longer known noun embedding the served noun
                # ("profit margin" vs "profit"), or an adjacent
                # compound of the two ("profit margin" built from
                # nouns 'profit' + 'margin') both mean the ask is
                # more specific than what was served.
                if o in noun and o != noun:
                    return noun
                if re.search(r"\b%s\s+%s\b" % (re.escape(o),
                                               re.escape(noun)), low) \
                        or re.search(r"\b%s\s+%s\b" % (re.escape(noun),
                                                       re.escape(o)),
                                     low):
                    return "%s+%s" % (o, noun)
    return None


def _requested_unit(text):
    """The unit the ask wants the ANSWER in. B29: the first version
    matched only '... in <unit>?' at the end; foreign authors write
    'Calculate, in kilojoules, the kinetic energy of ...' and the
    engine served joules -- a 1000x wrong answer past a guard that
    existed for exactly this. Now matched anywhere; two DIFFERENT
    requested units is ambiguous and returns the sentinel '?' so the
    caller escalates."""
    found = {_UNIT_WORDS[m.group(1).lower()]
             for m in _REQ_UNIT.finditer(text)}
    if not found:
        return None
    if len(found) > 1:
        return "?"
    return found.pop()


_VALUE_NUM = re.compile(
    r"(?<![\^/\w])(-?\d+(?:\.\d+)?)(?!\s*(?:st|nd|rd|th)\b)")


def _stated_values(text):
    """Numbers stated as quantities in the text, with unit-exponent
    digits (m/s^2, m^3) excluded by the lookbehind."""
    return [float(x) for x in _VALUE_NUM.findall(text)]


def _unbound_stated_quantity(text, rec):
    """A number the text states that no CERTIFIED/DERIVED fact carries
    means the parse is INCOMPLETE -- the serve about to happen ignored
    a stated quantity (dev finding 2026-09-03: unparsed acceleration
    left mass alone in state and weight m*g was served as 'force').
    An incomplete read never serves. Returns the orphan value or
    None."""
    st = rec.get("_state")
    if st is None:
        return None
    bound = set()
    for f in st.facts:
        # only a CERTIFIED/DERIVED fact counts as read: a QUARANTINED
        # fact holding a stated value means the engine SAW the
        # quantity and decided not to trust it -- serving a different
        # derivation while that fact sits quarantined answers a
        # different question than the one asked (dev finding: accel
        # QUARANTINED, weight m*g served as 'force').
        if f.get("value") is not None and \
                f.get("status") in ("CERTIFIED", "DERIVED"):
            bound.add(round(float(f["value"]), 6))
    for v in _stated_values(text):
        if round(v, 6) not in bound:
            return v
    return None


def _leaf_for_tierA(rec):
    """Taxonomy address for a Tier A serve, from evidence:
    output concept -> candidate caps -> input-presence filter.
    Returns (leaf, basis) or (None, why)."""
    info = rec.get("_info") or {}
    concept = info.get("target_concept")
    if not concept:
        return None, "no target concept in record"
    cands = [(name, c) for name, c in _CAPS.items()
             if (c.get("spec") or {}).get("output") == concept]
    if not cands:
        return None, "no capability outputs %r" % concept
    leaves = {taxonomy16.leaf_of_capability(n) for n, _ in cands}
    if len(leaves) == 1:
        return leaves.pop(), "unique output concept"
    # disambiguate by inputs present in the certified state
    st = rec.get("_state")
    present = set()
    if st is not None:
        for f in st.facts:
            if f["status"] in ("CERTIFIED", "DERIVED") and \
                    f.get("concept"):
                present.add(f["concept"])
    live = [(n, set((c.get("spec") or {}).get("inputs") or []))
            for n, c in cands
            if set((c.get("spec") or {}).get("inputs") or []) <= present]
    # dominance: a cap whose inputs are a PROPER subset of another live
    # cap's inputs is dropped -- the engine's planner derives from the
    # maximal certified evidence (m*a beats m*g_default when accel is
    # certified in state), and the served value came from that path.
    keep = [(n, ins) for n, ins in live
            if not any(ins < ins2 for _, ins2 in live)]
    lv = {taxonomy16.leaf_of_capability(n) for n, _ in keep}
    if len(lv) == 1:
        return lv.pop(), "inputs-present disambiguation"
    return None, "ambiguous address: %s" % sorted(
        leaves if not lv else lv)


def _try_symbolic(text, t0):
    task = sciparse16.parse(text)
    if task is None:
        return None
    leaf = taxonomy16.place_symbolic(task)
    if leaf is None or taxonomy16.executor(leaf) != "symcore16":
        return None
    task = dict(task)
    task["leaf"] = leaf
    val, cert = symcore16.solve(task)
    if val is not None:
        return {"status": SERVED, "value": val, "path": "symcore16",
                "leaf": leaf, "op": task["op"],
                "witness": cert["witness"]["check"],
                "ms": (time.perf_counter() - t0) * 1e3}
    return {"status": ESCALATED, "value": None,
            "path": "symcore16-refused", "reason": cert.get("why"),
            "ms": (time.perf_counter() - t0) * 1e3}


def ask16(text, qid=None):
    t0 = time.perf_counter()
    eng = _boot()
    rec = eng.run_query(text, qid or "q16")
    if rec.get("status") == "pm_answer":
        # choice-ask guard: a comparison is never answered by a number
        if CHOICE_ASK.search(text):
            return {"status": ESCALATED, "value": None,
                    "path": "tierA-guarded",
                    "reason": "choice ask, numeric serve refused",
                    "ms": (time.perf_counter() - t0) * 1e3}
        orphan = _unbound_stated_quantity(text, rec)
        if orphan is not None:
            return {"status": ESCALATED, "value": None,
                    "path": "tierA-guarded",
                    "reason": "stated quantity %g not bound by the "
                              "parse: incomplete read" % orphan,
                    "ms": (time.perf_counter() - t0) * 1e3}
        info = (rec.get("_info") or {})
        concept = info.get("target_concept")
        spec = _more_specific_asked(text, concept) if concept else None
        if spec:
            return {"status": ESCALATED, "value": None,
                    "path": "tierA-guarded",
                    "reason": "more specific concept asked: %r" % spec,
                    "ms": (time.perf_counter() - t0) * 1e3}
        value = rec.get("numeric_value")
        served_unit = (_KINDS.get(concept) or {}).get("unit") or ""
        req = _requested_unit(text)
        if req == "?":
            return {"status": ESCALATED, "value": None,
                    "path": "tierA-guarded",
                    "reason": "two different answer units requested",
                    "ms": (time.perf_counter() - t0) * 1e3}
        if req and _UREG is not None and req != served_unit:
            # honor the requested unit deterministically or hand on
            try:
                value = float((value * _UREG(served_unit)).to(req)
                              .magnitude)
                served_unit = req
            except Exception:
                return {"status": ESCALATED, "value": None,
                        "path": "tierA-guarded",
                        "reason": "asked in %r, derived %r, no "
                                  "deterministic conversion"
                                  % (req, served_unit),
                        "ms": (time.perf_counter() - t0) * 1e3}
        elif req and _UREG is None and req != served_unit:
            return {"status": ESCALATED, "value": None,
                    "path": "tierA-guarded",
                    "reason": "requested unit, converter unavailable",
                    "ms": (time.perf_counter() - t0) * 1e3}
        leaf, basis = _leaf_for_tierA(rec)
        return {"status": SERVED, "value": value, "path": "tierA",
                "leaf": leaf, "leaf_basis": basis, "unit": served_unit,
                "mode": rec.get("mode"),
                "ms": (time.perf_counter() - t0) * 1e3}

    reason = rec.get("abstain_reason") or "no_answer"
    hazards = []
    st = rec.get("_state")
    if st is not None:
        hazards = [f["fid"] for f in st.facts
                   if f["status"] in ("CONFLICTED", "AMBIGUOUS")]

    # ---- symbolic path (before the hazard verdict sticks) ---------
    # Tier A's fact reader sees "x = 3" in calculator register as
    # conflicting facts (probe finding). The symbolic path has its own
    # parser and witness gate; if it can take the query, its verdict
    # outranks a hazard raised by misreading algebra as narrative.
    sym = _try_symbolic(text, t0)
    if sym is not None and sym["status"] == SERVED:
        return sym

    if reason in HAZARD_REASONS or hazards:
        return {"status": ABSTAINED, "value": None, "path": "tierA",
                "reason": reason, "hazards": len(hazards),
                "ms": (time.perf_counter() - t0) * 1e3}
    if sym is not None:
        return sym
    return {"status": ESCALATED, "value": None, "path": "none",
            "reason": reason,
            "ms": (time.perf_counter() - t0) * 1e3}


if __name__ == "__main__":
    DEMO = [
        "A car of mass 1200 kg accelerates at 3 m/s^2. "
        "What force acts on it?",
        "find the second derivative of exp(x)*cos(x)",
        "What is the derivative of x^2 + 3x at x = 2?",
        "integrate x^2 from 0 to 3",
        "solve x^2 - 5x + 6 = 0",
        "gcd of 45 and 27",
        "is 97 prime?",
        "A waiter had 47 customers. If 41 left and he got another "
        "20, how many customers does he have?",
    ]
    for q in DEMO:
        r = ask16(q)
        print("%-48s -> %-9s %-12s leaf=%s value=%s"
              % (q[:48], r["status"], r.get("path"),
                 str(r.get("leaf"))[:52], str(r.get("value"))[:20]))
