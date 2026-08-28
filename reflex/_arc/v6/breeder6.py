# -*- coding: utf-8 -*-
"""V0.6 multi-target breeder (spec Sections 11, 12, 14, 22).

Learning targets from the SAME experience stream:
  T1 PATTERNS      QPAT/APAT via structural-alignment mining (align.py):
                   an escalated LLM answer becomes evidence ONLY when a
                   unique typed derivation over the query's own numbers
                   reproduces it deterministically.
  T2 CONCEPTS      lexeme->concept lexicon entries from the wildcard
                   tokens of aligned contexts (count nouns, ask verbs).
  T3 CAPABILITIES  the V0.5 robust dominant-cluster miner + LLM proposal
                   (imported unchanged) over accepted-handoff
                   observations.
  T4 LINKS         directed capability pairs (A.output consumed by B)
                   mined from successful plan paths, typed-checked,
                   support-thresholded.
  T5 COMPOSITIONS  repeated subchains -> composite expr capability by
                   symbolic substitution, validated by exact equivalence
                   against the primitive chain on fresh draws.

Methods comparison (spec 22) and the raw-answer memorization negative
control reuse the V0.5 implementations on the same traffic.

TRUST (spec 14): observation weight tiers, ablatable:
  1.0  alignment-verified full-LLM observations (deterministically
       reproduced) and handoff observations whose expression was
       re-evaluated consistently across >=2 distinct value tuples
  0.5  singleton accepted-handoff observations
Weights multiply cluster support in the T3 validator when trust is on.
"""
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4 import registry_v4 as R4                 # noqa: E402
from v4.registry_v4 import _KV                   # noqa: E402
from v3.ir import Quantity                       # noqa: E402
from v5.breeder5 import (breed_generation as breed_caps_generation,  # noqa
                         observations_from_records)
from v6.align import align                       # noqa: E402
from v6.patterns import (PatternRegistry, number_contexts,  # noqa
                         question_abstraction, tokenize, _abstract_token)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ======================================================================
# T1 + T2: pattern & lexeme mining via structural alignment
# ======================================================================
def mine_patterns(recs, items_by_id, registry, pr, max_records=None):
    """Consume escalation records (full-LLM answers) -> evidence into a
    PatternRegistry (candidates only; deployment is gates6's job).
    Returns mining stats."""
    stats = {"records_seen": 0, "full_llm": 0, "aligned_unique": 0,
             "aligned_merged": 0, "ambiguous": 0, "no_match": 0,
             "qpat_evidence": 0, "apat_evidence": 0,
             "lexeme_evidence": 0}
    for rec in (recs[:max_records] if max_records else recs):
        if rec.get("status") != "llm_answer" or not rec.get("answer"):
            continue
        stats["records_seen"] += 1
        it = items_by_id.get(rec.get("query_id")) or {}
        query = rec.get("query") or it.get("query") or ""
        if not query:
            continue
        stats["full_llm"] += 1
        ncs = number_contexts(query)
        r1 = None
        tr = rec.get("recognition") or {}
        if tr.get("r1_kinds"):
            r1 = []
            used = set()
            for nc in ncs:
                k = None
                for j, (kind, val) in enumerate(tr["r1_kinds"]):
                    if j not in used and abs(val - nc["value"]) < 1e-9:
                        k = kind
                        used.add(j)
                        break
                r1.append(k)
        res = align(ncs, rec["answer"], registry=registry, r1_kinds=r1)
        if not res["matches"]:
            stats["no_match"] += 1
            continue
        if not res["unique"]:
            stats["ambiguous"] += 1
            continue
        m = res["matches"][0]
        stats["aligned_unique"] += 1
        if m.get("merged_ambiguity"):
            stats["aligned_merged"] += 1
        value_tuple = tuple(sorted(
            ncs[i]["value"] for i, u in enumerate(m["used"]) if u))
        qid = rec.get("query_id", "?")
        for i, usedf in enumerate(m["used"]):
            if not usedf:
                continue
            kind = m["assignment"][i]
            nc = ncs[i]
            for g in (3, 2, 1):
                win, pos = nc["windows"][g]
                if pr.add_qpat_evidence(win, pos, kind, value_tuple,
                                        qid, True):
                    stats["qpat_evidence"] += 1
            # lexemes: wildcard tokens inside the tightest window
            toks = nc["raw_context"].split()
            for t in toks:
                if _abstract_token(t) in ("<NOUNS>", "<W>"):
                    if pr.add_lexeme_evidence(t, kind, qid, True):
                        stats["lexeme_evidence"] += 1
        q_abs = question_abstraction(query)
        if pr.add_apat_evidence(q_abs, m["goal_kind"], qid, True):
            stats["apat_evidence"] += 1
        segs = re.split(r"[.!]", query)
        qsent = segs[-1] if segs and segs[-1].strip() else query
        for t in tokenize(qsent):
            if _abstract_token(t) in ("<W>", "<NOUNS>"):
                if pr.add_lexeme_evidence(t, m["goal_kind"], qid, True):
                    stats["lexeme_evidence"] += 1
    return stats


# ======================================================================
# T3 wrapper: signature-grouped capability breeding (bug audit #4).
# Re-keyed goal-direct 'money' observations mix families (energy vs
# paint vs discount states), and the V0.5 miner intersects state kinds
# across ALL observations of a target -> empty intersection -> zero
# fits. Group money-target observations by their state-kind signature
# and mine each group separately; merged candidates flow through the
# SAME build/gate stack (collision, wrong-fire, validation-truth).
# ======================================================================
def breed_caps_grouped(recs, traffic_items, current_reg, gen_idx):
    from v5.breeder5 import (breed_trace_mining_robust,
                             breed_llm_proposal_robust, breed_raw_answer,
                             build_generation, safety_gate)
    from v4 import registry_v4 as _R4
    obs = observations_from_records(recs)
    groups = defaultdict(list)
    for o in obs:
        if o["target"] == "money":
            sig = tuple(sorted(o["state"]))
            groups[("money", sig)].append(o)
        else:
            groups[(o["target"], None)].append(o)
    mined, prop = [], []
    bred_outputs = {spec["output"] for name, spec in current_reg.items()
                    if name.startswith("bred_")}
    for (target, sig), rows in groups.items():
        if len(rows) < 5:
            continue
        m, _meta = breed_trace_mining_robust(rows)
        mined += m
        got = {c["output"] for c in m} | bred_outputs
        rows_new = [o for o in rows if o["target"] not in got]
        if rows_new:
            p, _pm = breed_llm_proposal_robust(rows_new)
            prop += p
    # dedupe by (inputs, output), mining first
    seen = set()
    cands_m, cands_p = [], []
    for c in mined:
        k = (tuple(sorted(c["inputs"])), c["output"])
        if k not in seen:
            seen.add(k)
            cands_m.append(c)
    for c in prop:
        k = (tuple(sorted(c["inputs"])), c["output"])
        if k not in seen:
            seen.add(k)
            cands_p.append(c)
    raw_c, raw_meta = breed_raw_answer(
        traffic_items, [r for r in recs
                        if r.get("numeric_value") is not None])
    reg_new, provenance = build_generation(current_reg, cands_m, cands_p,
                                           gen_idx)
    reg_final, gate = safety_gate(reg_new, current_reg, gen_idx)
    stats = {"generation": gen_idx, "observations": len(obs),
             "obs_groups": {f"{t}|{len(s) if s else '-'}": len(rows)
                            for (t, s), rows in groups.items()},
             "mined": len(cands_m), "proposed": len(cands_p),
             "raw_answer_candidates": len(raw_c),
             "provenance": provenance, "gate": gate,
             "new_caps_deployed": sorted(set(reg_final)
                                         - set(current_reg)),
             "registry_hash": _R4.registry_hash(reg_final),
             "created_at": _now()}
    return reg_final, stats


# ======================================================================
# T4: capability-link mining from successful plan paths
# ======================================================================
def mine_links(recs, registry, min_support=8):
    """Directed edges (A -> B): A's output kind is one of B's inputs and
    the pair appeared adjacently in successful plans. Typed check against
    the registry; support counted over distinct queries."""
    support = defaultdict(set)
    for rec in recs:
        if rec.get("status") not in ("reflex_answer", "partial_answer"):
            continue
        path = [p for p in (rec.get("path") or [])
                if not str(p).startswith("LLM[")]
        for a, b in zip(path, path[1:]):
            if a in registry and b in registry:
                support[(a, b)].add(rec.get("query_id"))
    cands = []
    for (a, b), qids in support.items():
        if len(qids) < min_support:
            continue
        sa, sb = registry[a], registry[b]
        if sa.get("transfer") or sb.get("transfer"):
            continue
        if sa["output"] not in sb["inputs"]:
            continue                      # typed-compatibility contract
        cands.append({"src": a, "dst": b, "via_kind": sa["output"],
                      "support": len(qids),
                      "contract": {"input": sa["output"],
                                   "precondition": f"produces {sa['output']}",
                                   "provenance": "trace_mined"},
                      "trace_ids": sorted(qids)[:20],
                      "created_at": _now()})
    return cands


# ======================================================================
# T5: composition mining — repeated subchains -> composite expr caps
# ======================================================================
def _compose_expr(chain, registry):
    """Symbolically compose chain [capA, capB, ...] into one expr over
    the composite's leaf inputs (in first-use order). Returns
    (inputs, output, expr) or None."""
    kind_expr = {}
    counts = {}
    leaf_inputs = []

    def leaf_var(kind):
        base = _KV.get(kind, kind[:2])
        i = counts.get(base, 0)
        counts[base] = i + 1
        return f"{base}{i}"

    for cap in chain:
        spec = registry[cap]
        expr = spec["expr"]
        # rename this cap's positional vars to the chain-level exprs
        local_counts = {}
        sub = {}
        for kind in spec["inputs"]:
            base = _KV.get(kind, kind[:2])
            i = local_counts.get(base, 0)
            local_counts[base] = i + 1
            var = f"{base}{i}"
            if kind in kind_expr:
                sub[var] = f"({kind_expr[kind]})"
            else:
                v = leaf_var(kind)
                leaf_inputs.append((kind, v))
                kind_expr[kind] = v
                sub[var] = v
        for var in sorted(sub, key=len, reverse=True):
            expr = re.sub(rf"\b{var}\b", sub[var], expr)
        kind_expr[spec["output"]] = expr
    out_kind = registry[chain[-1]]["output"]
    # re-index leaf vars into the executor's naming for the final input
    # order: rebuild with canonical numbering
    inputs = [k for k, _ in leaf_inputs]
    final_expr = kind_expr[out_kind]
    ren = {}
    counts2 = {}
    for kind, var in leaf_inputs:
        base = _KV.get(kind, kind[:2])
        i = counts2.get(base, 0)
        counts2[base] = i + 1
        ren[var] = f"{base}{i}"
    for var in sorted(ren, key=len, reverse=True):
        final_expr = re.sub(rf"\b{var}\b", ren[var], final_expr)
    return inputs, out_kind, final_expr


def mine_compositions(recs, registry, min_support=15, min_len=3,
                      rng_seed=7):
    """Repeated interior subchains -> composite capability candidates,
    validated by EXACT equivalence against the primitive chain on 25
    fresh random draws (deterministic, no LLM)."""
    import random
    rng = random.Random(rng_seed)
    support = defaultdict(set)
    for rec in recs:
        if rec.get("status") not in ("reflex_answer", "partial_answer"):
            continue
        path = [p for p in (rec.get("path") or [])
                if not str(p).startswith("LLM[")]
        for ln in range(min_len, min(len(path), 5) + 1):
            for s in range(0, len(path) - ln + 1):
                support[tuple(path[s:s + ln])].add(rec.get("query_id"))
    cands = []
    for chain, qids in sorted(support.items(),
                              key=lambda kv: -len(kv[1])):
        if len(qids) < min_support:
            continue
        if any(c not in registry for c in chain):
            continue
        try:
            inputs, out_kind, expr = _compose_expr(list(chain), registry)
        except Exception:
            continue
        if len(inputs) > 6:
            continue
        # equivalence validation on fresh draws
        ok = True
        for _ in range(25):
            vals = {k: rng.uniform(1, 50) for k in inputs}
            ins = {k: Quantity(kind=k, value=v) for k, v in vals.items()}
            # primitive chain
            have = {k: v for k, v in vals.items()}
            good = True
            for cap in chain:
                spec = registry[cap]
                if not all(k in have for k in spec["inputs"]):
                    good = False
                    break
                cins = {k: Quantity(kind=k, value=have[k])
                        for k in spec["inputs"]}
                v, okx, _ = R4.execute(cap, cins, registry=registry)
                if not okx:
                    good = False
                    break
                have[spec["output"]] = v
            if not good:
                ok = False
                break
            comp_spec = {"inputs": inputs, "output": out_kind,
                         "expr": expr, "equation": "composite"}
            tmp = dict(registry)
            tmp["__comp__"] = comp_spec
            v2, ok2, _ = R4.execute("__comp__", ins, registry=tmp)
            if not ok2 or abs(v2 - have[out_kind]) > 1e-6 * max(
                    1.0, abs(have[out_kind])):
                ok = False
                break
        if ok:
            cands.append({"chain": list(chain), "inputs": inputs,
                          "output": out_kind, "expr": expr,
                          "support": len(qids),
                          "equivalence_checked": 25,
                          "created_at": _now()})
    # drop chains subsumed by an accepted longer chain
    cands.sort(key=lambda c: (-len(c["chain"]), -c["support"]))
    kept = []
    for c in cands:
        if not any(" ".join(c["chain"]) in " ".join(k["chain"])
                   for k in kept):
            kept.append(c)
    return kept[:6]
