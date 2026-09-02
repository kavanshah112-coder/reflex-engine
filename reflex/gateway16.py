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
import time
from pathlib import Path

from . import sciparse16, symcore16, taxonomy16

SERVED = "SERVED"
ESCALATED = "ESCALATED"
ABSTAINED = "ABSTAINED"

HAZARD_REASONS = {"invariant_violation", "redundancy_mismatch",
                  "target_entity_ambiguous"}

_ENGINE = None
_CAPS = None


def _boot():
    global _ENGINE, _CAPS
    if _ENGINE is None:
        from .engine import Engine
        _ENGINE = Engine()
        _CAPS = json.loads(
            (Path(__file__).resolve().parents[1] / "packs" / "physics" /
             "caps.json").read_text(encoding="utf-8"))
    return _ENGINE


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


def ask16(text, qid=None):
    t0 = time.perf_counter()
    eng = _boot()
    rec = eng.run_query(text, qid or "q16")
    if rec.get("status") == "pm_answer":
        leaf, basis = _leaf_for_tierA(rec)
        out = {"status": SERVED, "value": rec.get("numeric_value"),
               "path": "tierA", "leaf": leaf, "leaf_basis": basis,
               "mode": rec.get("mode")}
        out["ms"] = (time.perf_counter() - t0) * 1e3
        return out
    reason = rec.get("abstain_reason") or "no_answer"
    hazards = []
    st = rec.get("_state")
    if st is not None:
        hazards = [f["fid"] for f in st.facts
                   if f["status"] in ("CONFLICTED", "AMBIGUOUS")]
    if reason in HAZARD_REASONS or hazards:
        return {"status": ABSTAINED, "value": None, "path": "tierA",
                "reason": reason, "hazards": len(hazards),
                "ms": (time.perf_counter() - t0) * 1e3}

    # ---- symbolic path -------------------------------------------
    task = sciparse16.parse(text)
    if task is not None:
        leaf = taxonomy16.place_symbolic(task)
        if leaf is not None and \
                taxonomy16.executor(leaf) == "symcore16":
            task = dict(task)
            task["leaf"] = leaf
            val, cert = symcore16.solve(task)
            if val is not None:
                return {"status": SERVED, "value": val,
                        "path": "symcore16", "leaf": leaf,
                        "op": task["op"],
                        "witness": cert["witness"]["check"],
                        "ms": (time.perf_counter() - t0) * 1e3}
            return {"status": ESCALATED, "value": None,
                    "path": "symcore16-refused",
                    "reason": cert.get("why"),
                    "ms": (time.perf_counter() - t0) * 1e3}

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
