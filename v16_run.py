# -*- coding: utf-8 -*-
# origin: new for V1.6 -- the evaluation runner (SPEC 8, 9)
"""One arm of V1.6 over one split, deterministically, no model calls.

  python v16_run.py --split dev [--data results/v16/data] [--limit N]
                    [--arm baseline]

Reports, per SPEC 8: served coverage + wrong-fire overall, per depth
rung, per taxonomy leaf, per register; escalation on distractors
(SAFETY-2 counter); certificates without addresses (SAFETY-1 counter);
latency. Grading rules:

  num    : |v - gold| <= max(1e-6*|gold|, 1e-6)
  list   : same multiset within tolerance (roots)
  bool   : equality
  expr   : the item's witness record grades the expression claim
           (numeric agreement at sample points -- no symbolic match)
  choice : the served label maps to the witness sign convention
           (+1 first option, -1 second, 0 equal)

A served answer that cannot be graded is WRONG (never quietly
dropped), and a served answer with no taxonomy address is WRONG by
SPEC 9 SAFETY-1 even when the value is right.
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))

import gold_independent as W  # noqa: E402


def grade(it, val):
    gt = it["gold_type"]
    wit = it["witness"]
    try:
        if gt == "expr":
            ok, _ = W.run_check(wit, str(val).replace(" + C", ""))
            return bool(ok)
        if gt == "choice":
            sign = {"a": 1.0, "b": -1.0, "equal": 0.0}.get(val)
            return sign is not None and sign == wit["expected"]
        if gt == "bool":
            return isinstance(val, bool) and val == bool(it["gold"])
        if gt == "list":
            g = it["gold"]
            return (isinstance(val, list) and len(val) == len(g) and
                    all(abs(a - b) <= max(1e-6 * abs(b), 1e-6)
                        for a, b in zip(sorted(val), sorted(g))))
        v, g = float(val), float(it["gold"])
        return abs(v - g) <= max(1e-6 * abs(g), 1e-6)
    except (TypeError, ValueError, KeyError):
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev",
                    choices=["acq", "dev", "seal"])
    ap.add_argument("--file", default=None,
                    help="evaluate an explicit item file (e.g. "
                         "ssci_dev.json) instead of a q100k split; "
                         "--split then only labels the output")
    ap.add_argument("--data", default=str(HERE / "results" / "v16" /
                                          "data"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--arm", default="baseline")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    src = (Path(a.data) / a.file) if a.file else \
        (Path(a.data) / ("q100k_%s.json" % a.split))
    if a.file:
        a.split = Path(a.file).stem
    items = json.loads(src.read_text(encoding="utf-8"))
    if a.limit:
        items = items[:a.limit]

    from reflex.gateway16 import ask16

    st = Counter()
    by_depth = defaultdict(Counter)
    by_leaf = defaultdict(Counter)
    by_reg = defaultdict(Counter)
    safety1 = []          # served without address (counted WRONG)
    safety2 = []          # distractor served (any correctness)
    wrong_rows = []
    rows = []
    t0 = time.perf_counter()
    for it in items:
        try:
            r = ask16(it["text"], it["id"])
        except Exception as exc:            # noqa: BLE001  (B27)
            # an engine exception is an escalation plus a logged
            # defect, never a dead run and never a serve
            st["engine_error"] += 1
            r = {"status": "ESCALATED", "value": None,
                 "path": "engine-error",
                 "reason": "%s: %s" % (type(exc).__name__,
                                       str(exc)[:120])}
        served = r["status"] == "SERVED"
        rec = {"id": it["id"], "status": r["status"],
               "path": r.get("path"), "leaf": r.get("leaf"),
               "depth": it.get("depth"),
               "register": it.get("register"),
               "distractor": it.get("distractor", False)}
        if r.get("reason"):
            rec["reason"] = str(r["reason"])[:120]
        dkey = ("dist" if it.get("distractor")
                else "d%s" % it.get("depth"))
        if served:
            if it.get("distractor"):
                st["SAFETY2_SERVED"] += 1
                safety2.append({"id": it["id"],
                                "text": it["text"][:100],
                                "value": str(r.get("value"))[:40]})
                rec["correct"] = False
            else:
                ok = grade(it, r["value"])
                noaddr = r.get("leaf") is None
                if noaddr:
                    st["SAFETY1_NO_ADDRESS"] += 1
                    safety1.append(it["id"])
                    ok = False
                rec["correct"] = ok
                st["served"] += 1
                st["correct" if ok else "WRONG"] += 1
                by_depth[dkey]["served"] += 1
                by_depth[dkey]["correct" if ok else "wrong"] += 1
                by_reg[it["register"]]["served"] += 1
                by_reg[it["register"]]["correct" if ok else
                                       "wrong"] += 1
                for lf in (it.get("leaves") or [r.get("leaf")]):
                    by_leaf[lf]["served"] += 1
                    by_leaf[lf]["correct" if ok else "wrong"] += 1
                if not ok:
                    wrong_rows.append({
                        "id": it["id"], "text": it["text"][:120],
                        "value": str(r.get("value"))[:60],
                        "gold": str(it.get("gold"))[:40],
                        "path": r.get("path"),
                        "leaf": r.get("leaf")})
        else:
            st[r["status"].lower()] += 1
            by_depth[dkey][r["status"].lower()] += 1
            by_reg[it.get("register", "?")][r["status"].lower()] += 1
            for lf in (it.get("leaves") or []):
                by_leaf[lf][r["status"].lower()] += 1
        rows.append(rec)
    wall = time.perf_counter() - t0

    n = len(items)
    n_dist = sum(1 for i in items if i.get("distractor"))
    n_in = n - n_dist
    served = st["served"]
    summ = {
        "arm": a.arm, "split": a.split, "n": n,
        "in_domain": n_in, "distractors": n_dist,
        "served": served, "correct": st["correct"],
        "WRONG": st["WRONG"],
        "coverage_in_domain": round(served / n_in, 4) if n_in else None,
        "wrong_fire": (round(st["WRONG"] / served, 5) if served
                       else None),
        "SAFETY1_no_address": st["SAFETY1_NO_ADDRESS"],
        "SAFETY2_distractor_served": st["SAFETY2_SERVED"],
        "escalated": st["escalated"], "abstained": st["abstained"],
        "engine_errors": st["engine_error"],
        "ms_per_query": round(1000 * wall / n, 3) if n else None,
        "model_calls": 0,
        "by_depth": {k: dict(v) for k, v in sorted(by_depth.items())},
        "by_register": {k: dict(v) for k, v in sorted(by_reg.items())},
    }
    out = HERE / "results" / "v16"
    out.mkdir(parents=True, exist_ok=True)
    tag = ("_%s" % a.tag) if a.tag else ""
    base = "%s_%s%s" % (a.arm, a.split, tag)
    (out / ("%s_summary.json" % base)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    (out / ("%s_by_leaf.json" % base)).write_text(
        json.dumps({k: dict(v) for k, v in sorted(by_leaf.items())},
                   indent=1), encoding="utf-8")
    (out / ("%s_wrong.json" % base)).write_text(
        json.dumps({"wrong": wrong_rows, "safety1": safety1,
                    "safety2": safety2}, indent=1), encoding="utf-8")
    with open(out / ("%s.jsonl" % base), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    print(json.dumps({k: v for k, v in summ.items()
                      if k not in ("by_depth", "by_register")},
                     indent=1))
    print("by_depth:", json.dumps(summ["by_depth"]))


if __name__ == "__main__":
    main()
