# -*- coding: utf-8 -*-
"""V0.6 staged deployment gates (spec Sections 15-19).

Pattern/lexeme candidates pass, in order:
  G1 structural   >= MIN_EV evidence items over >= MIN_DISTINCT distinct
                  value tuples (patterns) / >= 2 sources (lexemes);
                  conflict ratio <= 0.1
  G2 batch probe  candidates deployed into a SANDBOX registry; the pure
                  engine runs the probe suite (revaluation + paraphrase
                  surfaces + negative-applicability) and the V0.4
                  validation set:
                    - zero wrong numerics anywhere
                    - zero numerics on negative/adversarial probes
                    - validation correct-count must not decrease
                  Implicated candidates (via recognition traces) are
                  dropped individually; if culprits cannot be identified
                  the whole batch is rejected.
  G3 anti-pattern any candidate implicated in a wrong record is BLOCKED
                  (recorded, never silently deleted).

Capabilities (T3) keep the V0.5 gate stack (dominant-cluster validator +
wrong-fire + validation-truth gates) — imported, not reimplemented.
Links/compositions carry their own typed/equivalence validation in the
miner; G2 applies to them through the engine run as well when deployed.

Sealed and external sets are NEVER touched here (spec 20).
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4.analyze_v4 import grade  # noqa: E402

MIN_EV = 3
MIN_DISTINCT = 3
MAX_CONFLICT = 0.10
MIN_LEX_SOURCES = 2


def g1_structural(pr):
    """Promote candidates -> 'staged' (in-memory) lists; returns keys."""
    q_keys, a_keys, l_keys = [], [], []
    for k, e in pr.qpats.items():
        if e["status"] != "candidate":
            continue
        distinct = {tuple(x["values"]) for x in e["evidence"]}
        tot = len(e["evidence"]) + e["conflicts"]
        if len(e["evidence"]) >= MIN_EV and \
                len(distinct) >= MIN_DISTINCT and \
                e["conflicts"] / max(1, tot) <= MAX_CONFLICT:
            q_keys.append(k)
    for k, e in pr.apats.items():
        if e["status"] != "candidate":
            continue
        srcs = {x["source"] for x in e["evidence"]}
        tot = len(e["evidence"]) + e["conflicts"]
        if len(srcs) >= MIN_EV and \
                e["conflicts"] / max(1, tot) <= MAX_CONFLICT:
            a_keys.append(k)
    for k, e in pr.lexicon.items():
        if e["status"] != "candidate":
            continue
        srcs = {x["source"] for x in e["evidence"]}
        tot = len(e["evidence"]) + e["conflicts"]
        if len(srcs) >= MIN_LEX_SOURCES and \
                e["conflicts"] / max(1, tot) <= MAX_CONFLICT:
            l_keys.append(k)
    return q_keys, a_keys, l_keys


def _sandbox(pr, q_keys, a_keys, l_keys):
    sb = copy.deepcopy(pr)
    for k in q_keys:
        sb.qpats[k]["status"] = "deployed"
    for k in a_keys:
        sb.apats[k]["status"] = "deployed"
    for k in l_keys:
        sb.lexicon[k]["status"] = "deployed"
    return sb


def _run_pure(engine, items):
    out = []
    for it in items:
        rec = engine.process(it["query"], mode_llm="pure",
                             query_id=it["id"])
        out.append((it, rec))
    return out


def g2_batch_probe(pr, q_keys, a_keys, l_keys, probes, val_items,
                   registry=None, max_iters=4):
    """Iteratively deploy the batch in a sandbox, drop implicated
    candidates, until clean or empty. Returns (final PatternRegistry,
    report)."""
    from v6.engine6 import V6Engine
    report = {"initial": {"qpats": len(q_keys), "apats": len(a_keys),
                          "lexemes": len(l_keys)},
              "dropped": [], "iterations": 0}
    # baseline correctness WITHOUT the batch (validation only)
    eng0 = V6Engine(pattern_registry=pr, mode="partial", integrity=True,
                    depaware=False, registry=registry)
    base_val = _run_pure(eng0, val_items)
    base_correct = sum(grade(it, r)[0] for it, r in base_val)
    while report["iterations"] < max_iters and \
            (q_keys or a_keys or l_keys):
        report["iterations"] += 1
        sb = _sandbox(pr, q_keys, a_keys, l_keys)
        eng = V6Engine(pattern_registry=sb, mode="partial",
                       integrity=True, depaware=False, registry=registry)
        culprits = set()
        wrongs = 0
        for it, rec in _run_pure(eng, probes + val_items):
            ok, _ = grade(it, rec)
            bad = ((rec.get("numeric_value") is not None and not ok)
                   or (rec.get("numeric_value") is not None
                       and it.get("unanswerable")))
            if bad:
                wrongs += 1
                tr = rec.get("recognition") or {}
                for p in tr.get("qpat_hits", []):
                    culprits.add(("Q", p))
                if tr.get("apat_hit"):
                    culprits.add(("A", tr["apat_hit"]))
                for t, _c in tr.get("lexeme_votes", []):
                    culprits.add(("L", t.lower()))
        val_correct = sum(grade(it, r)[0] for it, r in
                          _run_pure(eng, val_items))
        if wrongs == 0 and val_correct >= base_correct:
            for k in q_keys:
                pr.qpats[k]["status"] = "deployed"
            for k in a_keys:
                pr.apats[k]["status"] = "deployed"
            for k in l_keys:
                pr.lexicon[k]["status"] = "deployed"
            report["deployed"] = {"qpats": len(q_keys),
                                  "apats": len(a_keys),
                                  "lexemes": len(l_keys)}
            report["val_correct"] = [base_correct, val_correct]
            return pr, report
        if not culprits:
            report["rejected_batch"] = True
            report["reason"] = (f"wrongs={wrongs}, val {val_correct} < "
                                f"base {base_correct}, no culprits "
                                "identifiable")
            return pr, report
        for fam, key in culprits:
            report["dropped"].append((fam, key))
            if fam == "Q" and key in q_keys:
                q_keys.remove(key)
                pr.block("Q", key, "g2_probe_implicated")
            elif fam == "A" and key in a_keys:
                a_keys.remove(key)
                pr.block("A", key, "g2_probe_implicated")
            elif fam == "L" and key in l_keys:
                l_keys.remove(key)
                pr.lexicon[key]["status"] = "blocked"
    report["deployed"] = {"qpats": 0, "apats": 0, "lexemes": 0}
    return pr, report


def deploy_patterns(pr, probes, val_items, registry=None):
    q, a, l = g1_structural(pr)
    return g2_batch_probe(pr, q, a, l, probes, val_items,
                          registry=registry)
