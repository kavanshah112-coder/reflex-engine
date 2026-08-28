"""V0.4 analysis: grading, Section 52/53/54 tables, statistics, failure
taxonomy. Produces results/analysis_v4.json; printing is a compact summary.
Grading mirrors V0.3 (numeric / correct-reject / rubric for LLM text)."""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401

from src.evaluation.grade import numeric_match, rubric_match  # noqa: E402

RAW = ROOT / "results" / "raw_v4"
DATA = ROOT / "data"

SYSTEMS = ["llm", "v3_dynamic_pure", "v3_dynamic_hybrid", "v4_static_pure",
           "v4_static", "v4_reflex_pure", "v4_partial_pure", "v4_aon",
           "v4_partial_h0", "v4_partial_h1", "v4_partial_h2",
           "v4_partial_h3", "v4_partial_unstruct", "v4_partial_noverify",
           "v4_partial_h1_handv1", "v4_partial_h2_handv1",
           "v4_partial_h3_handv1", "v4_partial_noverify_handv1",
           "v4_partial_h2_noise5", "v4_partial_h2_noise10",
           "v4_partial_h2_noise20", "v4_partial_h2_exec5",
           "v4_partial_h2_exec10", "v4_partial_h2_exec20"]


def items_by_id(split="test"):
    return {i["id"]: i for i in json.loads(
        (DATA / f"v0.4_{split}.json").read_text(encoding="utf-8"))}


def bucket(it):
    if it["domains"] == ["ood"]:
        return "ood"
    if it.get("unanswerable"):
        return "adv"
    return it["coverage_bucket"]


def is_llm_final(rec):
    return rec.get("status") == "llm_answer"


def grade(it, rec):
    """(correct, method). Mirrors v3: OOD/unanswerable need refusal (reflex)
    or rubric-matching text (LLM); numeric items match value or text."""
    llm_final = is_llm_final(rec)
    if it["domains"] == ["ood"] or it.get("unanswerable"):
        if llm_final:
            return (rubric_match(it["rubric"], rec.get("answer") or ""),
                    "rubric")
        return (rec.get("numeric_value") is None
                and rec.get("status") in ("ABSTAIN", "REFLEX_FAILURE"),
                "correct_reject")
    na = it["numeric_answer"]
    if rec.get("numeric_value") is not None:
        return (numeric_match(na["value"], na["tol"],
                              value=rec["numeric_value"]), "numeric")
    if llm_final:
        return (numeric_match(na["value"], na["tol"],
                              text=rec.get("answer")), "numeric_text")
    return (False, "no_answer")


def load(tag):
    p = RAW / f"{tag}.jsonl"
    if not p.exists():
        return None
    out = {}
    for l in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(l)
        # V0.3-adapter records keep LLM usage in a nested dict — normalize
        if "llm" in r and isinstance(r["llm"], dict) \
                and "llm_tokens" not in r:
            r["llm_calls"] = 1
            r["llm_tokens"] = (r["llm"].get("prompt_tokens", 0)
                               + r["llm"].get("gen_tokens", 0))
            r["llm_flops"] = r["llm"].get("flops_est", 0.0)
        out[r["query_id"]] = r
    return out


def pct(xs, q):
    return float(np.percentile(xs, q)) if xs else float("nan")


def sys_row(items, recs):
    row = {"n": 0, "correct": 0, "by_bucket": defaultdict(lambda: [0, 0]),
           "llm_calls": 0, "llm_tokens": 0, "llm_flops": 0.0,
           "reflex_flops": 0.0, "no_llm_queries": 0, "wrong_numeric": 0,
           "lat": []}
    per_item = {}
    for qid, it in items.items():
        r = recs.get(qid)
        if r is None:
            continue
        ok, method = grade(it, r)
        row["n"] += 1
        row["correct"] += ok
        b = bucket(it)
        row["by_bucket"][b][0] += ok
        row["by_bucket"][b][1] += 1
        row["llm_calls"] += r.get("llm_calls", 0)
        row["llm_tokens"] += r.get("llm_tokens", 0)
        row["llm_flops"] += r.get("llm_flops", 0.0) or 0.0
        row["reflex_flops"] += r.get("reflex_flops", 0.0) or 0.0
        row["no_llm_queries"] += (r.get("llm_calls", 0) or 0) == 0
        if method == "numeric" and not ok:
            row["wrong_numeric"] += 1
        row["lat"].append(r.get("total_ms", 0.0) or 0.0)
        per_item[qid] = ok
    if row["n"] == 0:
        return None, {}
    out = {"n": row["n"], "acc": row["correct"] / row["n"],
           "by_bucket": {b: {"acc": c / t, "n": t}
                         for b, (c, t) in sorted(row["by_bucket"].items())},
           "llm_calls": row["llm_calls"], "llm_tokens": row["llm_tokens"],
           "llm_avoidance": row["no_llm_queries"] / row["n"],
           "wrong_numeric": row["wrong_numeric"],
           "flops_llm": row["llm_flops"], "flops_reflex": row["reflex_flops"],
           "lat_p50": pct(row["lat"], 50), "lat_p90": pct(row["lat"], 90),
           "lat_p95": pct(row["lat"], 95), "lat_p99": pct(row["lat"], 99)}
    return out, per_item


def mcnemar(a, b):
    """Exact binomial McNemar on shared ids."""
    ids = sorted(set(a) & set(b))
    b01 = sum(1 for i in ids if a[i] and not b[i])
    b10 = sum(1 for i in ids if not a[i] and b[i])
    n = b01 + b10
    if n == 0:
        return {"b01": 0, "b10": 0, "p": 1.0}
    k = min(b01, b10)
    p = sum(math.comb(n, j) for j in range(0, k + 1)) / 2 ** n * 2
    return {"b01": b01, "b10": b10, "p": min(1.0, p)}


def bootstrap_delta(a, b, n_boot=10000, seed=42):
    ids = sorted(set(a) & set(b))
    rng = np.random.default_rng(seed)
    av = np.array([a[i] for i in ids], dtype=float)
    bv = np.array([b[i] for i in ids], dtype=float)
    deltas = []
    for _ in range(n_boot):
        s = rng.integers(0, len(ids), len(ids))
        deltas.append(av[s].mean() - bv[s].mean())
    return {"delta": float(av.mean() - bv.mean()),
            "ci95": [float(np.percentile(deltas, 2.5)),
                     float(np.percentile(deltas, 97.5))]}


def partial_metrics(items, recs):
    """Section 54 metrics for a partial-mode system."""
    m = {"partial_answers": 0, "partial_correct": 0,
         "handoffs_total": 0, "handoffs_accepted": 0,
         "handoff_valid_frac": None, "unknown_detect": [0, 0],
         "reflex_contrib": [], "escalation_full_llm": 0}
    valid = tot = 0
    for qid, it in items.items():
        r = recs.get(qid)
        if r is None:
            continue
        hs = r.get("handoffs", [])
        m["handoffs_total"] += len(hs)
        m["handoffs_accepted"] += sum(1 for h in hs if h.get("accepted"))
        for h in hs:
            tot += 1
            valid += "ok" in (h.get("validation") or [])
        if r.get("status") == "llm_answer":
            m["escalation_full_llm"] += 1
        has_unknown = any(not s.get("known", True)
                          for s in it.get("gt_graph") or [])
        if has_unknown and not it.get("unanswerable") \
                and it["domains"] != ["ood"]:
            m["unknown_detect"][1] += 1
            # detected = did NOT emit a plain reflex answer over the gap
            if r.get("status") != "reflex_answer":
                m["unknown_detect"][0] += 1
        if r.get("status") == "partial_answer":
            m["partial_answers"] += 1
            ok, _ = grade(it, r)
            m["partial_correct"] += ok
            path = r.get("path") or []
            nl = sum(1 for s in path if str(s).startswith("LLM["))
            if path:
                m["reflex_contrib"].append(1 - nl / len(path))
    m["handoff_valid_frac"] = valid / tot if tot else None
    m["reflex_contrib"] = (float(np.mean(m["reflex_contrib"]))
                           if m["reflex_contrib"] else None)
    return m


def interior_unknown(it):
    """Section 62 core-experiment membership: gt graph has a known prefix
    AND a known suffix around at least one unknown step (A->B->X->C->D)."""
    g = it.get("gt_graph") or []
    ks = [s.get("known", True) for s in g]
    return any(not k and any(ks[:i]) and any(ks[i + 1:])
               for i, k in enumerate(ks))


def core_experiment(items, systems_recs):
    """Per-system metrics on the interior-unknown subset."""
    sub = {qid: it for qid, it in items.items() if interior_unknown(it)}
    out = {"n": len(sub), "ids": sorted(sub)}
    for name, recs in systems_recs.items():
        if recs is None:
            continue
        acc = ltok = lcall = rflop = lflop = wrong = n = 0
        for qid, it in sub.items():
            r = recs.get(qid)
            if r is None:
                continue
            n += 1
            ok, method = grade(it, r)
            acc += ok
            wrong += (method == "numeric" and not ok)
            ltok += r.get("llm_tokens", 0) or 0
            lcall += r.get("llm_calls", 0) or 0
            rflop += r.get("reflex_flops", 0.0) or 0.0
            lflop += r.get("llm_flops", 0.0) or 0.0
        if n:
            out[name] = {"n": n, "acc": acc / n, "llm_tokens": ltok,
                         "llm_calls": lcall, "wrong_numeric": wrong,
                         "flops_reflex": rflop, "flops_llm": lflop}
    return out


def domain_accuracy(items, recs):
    by = defaultdict(lambda: [0, 0])
    for qid, it in items.items():
        r = recs.get(qid)
        if r is None or it.get("unanswerable") or it["domains"] == ["ood"]:
            continue
        ok, _ = grade(it, r)
        for d in it["domains"]:
            by[d][0] += ok
            by[d][1] += 1
    return {d: {"acc": c / t, "n": t} for d, (c, t) in sorted(by.items())}


def main():
    items = items_by_id("test")
    rows, per = {}, {}
    for s in SYSTEMS:
        recs = load(s)
        if recs is None:
            continue
        row, pi = sys_row(items, recs)
        if row:
            rows[s] = row
            per[s] = pi
    pmetrics = {s: partial_metrics(items, load(s))
                for s in ["v4_partial_h1", "v4_partial_h2", "v4_partial_h3",
                          "v4_partial_unstruct", "v4_partial_noverify"]
                if load(s)}
    stats = {}
    pairs = [("v4_partial_h2", "v4_aon"), ("v4_partial_h2", "llm"),
             ("v4_partial_h2", "v4_static"), ("v4_aon", "llm"),
             ("v4_partial_h2", "v4_partial_unstruct"),
             ("v4_partial_h2", "v4_partial_noverify"),
             ("v4_partial_h2", "v4_partial_h2_handv1"),
             ("v4_partial_h2_handv1", "v4_partial_unstruct")]
    for a, b in pairs:
        if a in per and b in per:
            stats[f"{a}_vs_{b}"] = {**mcnemar(per[a], per[b]),
                                    **bootstrap_delta(per[a], per[b])}
    core = core_experiment(items, {s: load(s) for s in
                                   ["llm", "v4_aon", "v4_partial_h2",
                                    "v4_partial_unstruct",
                                    "v4_partial_noverify"]})
    domains = {s: domain_accuracy(items, load(s))
               for s in ["llm", "v4_partial_h2", "v4_reflex_pure"]
               if load(s)}
    out = {"systems": rows, "partial_metrics": pmetrics, "stats": stats,
           "core_experiment": core, "domain_accuracy": domains}
    (ROOT / "results" / "analysis_v4.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"{'system':26s} {'acc':>6s} {'avoid':>6s} {'llm_tok':>8s} "
          f"{'p50ms':>8s}")
    for s, r in rows.items():
        print(f"{s:26s} {r['acc']:6.3f} {r['llm_avoidance']:6.2f} "
              f"{r['llm_tokens']:8d} {r['lat_p50']:8.0f}")
    for k, v in stats.items():
        print(f"  {k}: delta={v['delta']:+.3f} ci={v['ci95']} p={v['p']:.4g}")


if __name__ == "__main__":
    main()
