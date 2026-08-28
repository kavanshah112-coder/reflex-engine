# -*- coding: utf-8 -*-
"""V0.11 execution adapter: certified semantic state -> Path Manager.

- entity-scoped execution: an entity-specific target consumes ONLY
  that entity's facts (+ GLOBAL); Invariant I3 enforced by
  construction and re-checked after execution;
- temporal-delta targets ("mass lost", "change in X"): initial -
  final (loss) computed deterministically from the temporal pair;
- relational targets ("difference in X between A and B", "total X",
  "which <comparative>"): per-entity computation then combination;
- ambiguity: deterministic resolution attempted (graph); else the
  optional LLM resolver PROPOSES a binding which integrity validates
  (Section 7 — the LLM never writes certified state); else abstain;
- selective redundancy (Section 10): high-risk paths (money target
  or plan length >= 10) re-derived via a second route with the
  primary route's capabilities removed where an alternative exists;
  disagreement > 1e-6 relative invalidates the result.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v10.pathman10 import LongPathManager          # noqa: E402
from v10.universe10 import build_registry10, KINDS10  # noqa: E402
from v10 import planner10 as PL10                  # noqa: E402
from v11.integrity11 import check_invariants       # noqa: E402
from v11.semstate11 import COMPARATIVES            # noqa: E402
from v8 import pathman as PM8                      # noqa: E402
from v10.universe10 import execute10               # noqa: E402

REG11 = build_registry10()
PM8.exec4 = lambda name, inputs, registry=None: \
    execute10(name, inputs, registry or REG11)

DELTA_RE = re.compile(
    r"\b(lost|gained|change in|difference in|drop in|increase in|"
    r"decrease in|delta)\b", re.I)
TOTAL_RE = re.compile(r"\b(total|combined|sum of|together)\b", re.I)
WHICH_RE = re.compile(r"\bwhich\b", re.I)

_CONV = {"min": 60.0, "minutes": 60.0, "minute": 60.0,
         "h": 3600.0, "hr": 3600.0, "hrs": 3600.0, "hour": 3600.0,
         "hours": 3600.0}


def _to_canonical(f):
    """FULL canonical conversion set, ported from the v9
    compile_state lineage (bug_audit B3: the original v11 adapter
    ported only a subset; the missing price_per_kwh $/kWh->$/J
    conversion produced 3.6e6-scaled energy costs on full chains)."""
    v = f["value"]
    u = (f.get("unit") or "").strip().lower().rstrip(".,;:!?")
    k = f["concept"]
    if k == "time" and u in _CONV:
        return v * _CONV[u]
    if k == "speed" and u in ("km/h", "kph", "km/hr"):
        return v / 3.6
    if k == "mass" and u in ("g", "grams", "gram"):
        return v / 1000.0
    if k == "mass" and u in ("t", "tonne", "tonnes", "metric tons"):
        return v * 1000.0
    if k == "energy" and u == "kj":
        return v * 1e3
    if k == "energy" and u == "mj":
        return v * 1e6
    if k == "energy" and u == "kwh":
        return v * 3.6e6
    if k == "power" and u == "kw":
        return v * 1e3
    if k == "price_per_kwh" and ("kwh" in u or u in ("$", "")):
        return v / 3.6e6
    if k == "solution_volume" and u in ("ml", "millilitres",
                                       "milliliters"):
        return v / 1000.0
    if u in ("%", "percent") and abs(v) > 1.5:
        from v10.universe10 import KINDS10 as K
        if k in K and all(d == 0 for d in K[k][0]):
            return v / 100.0
    return v


def _lpm_solve(facts, target, query, qid, avail=None, use_llm=False):
    state = [{"kind": f["concept"], "value": _to_canonical(f),
              "clause": -1, "provenance": "query",
              "consumed": False, "fid": f["fid"],
              "entity": f.get("entity")} for f in facts]
    lpm = LongPathManager(REG11, use_llm=use_llm, available=avail)
    r = lpm.run(state, target, query, qid)
    return r


def run(state, info, query, qid, ask=None, use_llm=False,
        resolver=None, redundancy=False, avail=None):
    """state: certified SemanticState. Returns record."""
    rec = {"query_id": qid, "status": None, "numeric_value": None,
           "mode": None, "resolver_used": False,
           "redundancy_checked": False, "invariant_violations": [],
           "llm_calls": [], "abstain_reason": None}
    ask = ask or query.split(".")[-1]
    t_concept = info.get("target_concept")
    t_entity = info.get("target_entity")
    if not t_concept or t_concept == "UNKNOWN":
        rec.update(status="abstain", abstain_reason="no_target")
        return rec

    # ambiguity resolution for facts the target NEEDS
    needed_amb = [f for f in state.facts
                  if f["status"] == "AMBIGUOUS"]
    if needed_amb and resolver is not None:
        for f in needed_amb:
            prop = resolver(query, f, state)
            if prop and prop in state.graph.entities:
                # validator: accept only if unambiguous under the
                # graph OR consistent with a unique same-concept gap
                f_ent_facts = [g for g in state.facts
                               if g["concept"] == f["concept"]
                               and g["status"] == "CERTIFIED"
                               and g["entity"] == prop]
                if not f_ent_facts:      # no conflict created
                    f["entity"] = prop
                    f["status"] = "CERTIFIED"
                    rec["resolver_used"] = True

    # delta target?
    m = DELTA_RE.search(ask)
    if m:
        scope = t_entity
        pair = [f for f in state.certified(scope)
                if f["concept"] == t_concept
                and f["temporal"] in ("initial", "final")]
        ini = [f for f in pair if f["temporal"] == "initial"]
        fin = [f for f in pair if f["temporal"] == "final"]
        if ini and fin:
            v = _to_canonical(ini[0]) - _to_canonical(fin[0])
            if m.group(1).lower() in ("gained", "increase in"):
                v = -v
            rec.update(status="pm_answer", numeric_value=v,
                       mode="temporal_delta")
            return rec
        rec.update(status="abstain",
                   abstain_reason="delta_pair_missing")
        return rec

    # relational: total / difference / which
    ents = sorted(state.graph.entities)
    if TOTAL_RE.search(ask) and len(ents) >= 2:
        vals = []
        for e in ents:
            r = _lpm_solve(state.certified(e), t_concept, query,
                           f"{qid}:{e}", avail, use_llm)
            if r.get("numeric_value") is None:
                rec.update(status="abstain",
                           abstain_reason=f"relational_part_{e}")
                return rec
            vals.append(r["numeric_value"])
        rec.update(status="pm_answer", numeric_value=sum(vals),
                   mode="relational_total")
        return rec
    if "difference" in ask.lower() and len(ents) >= 2:
        vals = []
        for e in ents[:2]:
            r = _lpm_solve(state.certified(e), t_concept, query,
                           f"{qid}:{e}", avail, use_llm)
            if r.get("numeric_value") is None:
                rec.update(status="abstain",
                           abstain_reason=f"relational_part_{e}")
                return rec
            vals.append(r["numeric_value"])
        rec.update(status="pm_answer",
                   numeric_value=abs(vals[0] - vals[1]),
                   mode="relational_difference")
        return rec

    # entity-scoped single solve; an ASSERTED value for the TARGET
    # concept itself is suspicious (corrupted-derived class): exclude
    # it and recompute from genuine inputs
    facts = [f for f in state.certified(t_entity)
             if f["concept"] != t_concept]
    if not facts:
        facts = state.certified(t_entity)
    if t_entity:
        # entity-specific beats GLOBAL for the same concept
        ent_kinds = {f["concept"] for f in facts
                     if f.get("entity") == t_entity}
        facts = [f for f in facts
                 if f.get("entity") == t_entity
                 or f["concept"] not in ent_kinds]
    if t_entity is None and info.get("target_candidates"):
        rec.update(status="abstain",
                   abstain_reason="target_entity_ambiguous")
        return rec
    r = _lpm_solve(facts, t_concept, query, qid, avail, use_llm)
    rec["mode"] = "entity_scoped" if t_entity else "global"
    rec["llm_calls"] = r.get("llm_calls", [])
    if r.get("status") == "pm_answer":
        # invariant re-check on consumed facts
        used = [f for f in facts]
        rec["invariant_violations"] = check_invariants(
            state, executed_inputs=used, target_entity=t_entity)
        if rec["invariant_violations"]:
            rec.update(status="abstain",
                       abstain_reason="invariant_violation")
            return rec
        val = r["numeric_value"]
        # selective redundancy
        plan_len = len(r.get("path") or [])
        from v10.universe10 import KINDS10 as K
        money = t_concept in K and K[t_concept][0][6] != 0
        if redundancy and (money or plan_len >= 10):
            rec["redundancy_checked"] = True
            used_caps = set(c for c in (r.get("path") or [])
                            if isinstance(c, str))
            alt_reg = {k: v for k, v in REG11.items()
                       if k not in used_caps}
            steps2, _ = PL10.plan(
                [f["concept"] for f in facts], t_concept, alt_reg,
                allow_gaps=False)
            if steps2 is not None:
                r2 = _lpm_solve(facts, t_concept, query,
                                f"{qid}:alt",
                                [s for s in steps2
                                 if isinstance(s, str)], False)
                v2 = r2.get("numeric_value")
                if v2 is not None and abs(v2 - val) > 1e-6 * max(
                        1.0, abs(val)):
                    rec.update(status="abstain",
                               abstain_reason="redundancy_mismatch")
                    return rec
        rec.update(status="pm_answer", numeric_value=val)
    else:
        rec.update(status="abstain",
                   abstain_reason=r.get("abstain_reason",
                                        "no_plan"))
    return rec
