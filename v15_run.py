# -*- coding: utf-8 -*-
# origin: new for V1.5 -- the pipeline runner (PLAN sections 3, 7)
"""One arm of V1.5, end to end, on sealed data.

  python v15_run.py --arm A6 --limit 400

Arms follow the plan's ablation table. The number that matters is
DETERMINISTIC COVERAGE -- queries answered correctly with no model call
-- because the plan's energy identity makes the saving essentially
equal to it:

    saving  ~=  1 - f_escalate  =  deterministic coverage

So this runner reports coverage, correctness and wrong-fire together.
Coverage bought with wrong answers is not coverage; it is the failure
mode every prior version of this arc has had to be talked out of.

No model is called here. Arms that would escalate record WHAT they
would have escalated and WHICH unit, so the escalation fraction and the
smallest-unit distribution are measured without spending anything. The
model arms run separately through the bridge.
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
DATA = HERE / "results" / "v15" / "data"
OUT = HERE / "results" / "v15"

ARMS = {
    "A2": {"index": False, "solve": False},   # worker only
    "A3": {"index": True, "solve": False},    # + substrate
    "A4": {"index": True, "solve": True},     # + path/execution
    "A6": {"index": True, "solve": True},     # full (same det. core)
    "A7": {"index": False, "solve": True},    # no relational structure
}


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    return abs(v) < 1e-9 if a == 0 else abs(v - a) / abs(a) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="A6", choices=sorted(ARMS))
    ap.add_argument("--split", default="s3_dev")
    ap.add_argument("--limit", type=int, default=400)
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex import (escalate as ESC, packet as PK,
                        packet_index as PI, v15exec)

    items = json.loads((DATA / ("%s.json" % a.split))
                       .read_text(encoding="utf-8"))[:a.limit]
    cfg = ARMS[a.arm]

    st = Counter()
    esc_units = Counter()
    abst = Counter()
    rows = []
    t0 = time.perf_counter()
    for it in items:
        q = it["q"]
        packet, info = PK.build(q, it["id"])
        rec = {"id": it["id"], "verdict": packet["verdict"],
               "answer": it.get("answer"), "value": None}

        if packet["verdict"] != PK.COMPLETE:
            unit = PK.escalation_unit(packet)["unit"]
            esc_units[unit] += 1
            st["escalated"] += 1
            rec["status"] = "escalated"
            rec["unit"] = unit
            rows.append(rec)
            continue

        if not cfg["index"]:
            st["no_index"] += 1
            rec["status"] = "no_index"
            rows.append(rec)
            continue

        state, irep = PI.index(packet, q)
        if not irep["spans_ok"]:
            st["abstained"] += 1
            abst["unverifiable_span"] += 1
            rec["status"] = "abstained"
            rows.append(rec)
            continue

        if not cfg["solve"]:
            st["indexed_only"] += 1
            rec["status"] = "indexed_only"
            rows.append(rec)
            continue

        value, trace = v15exec.solve(state, packet)
        if value is None:
            st["abstained"] += 1
            abst[trace.get("why", "?")] += 1
            rec["status"] = "abstained"
            rec["why"] = trace.get("why")
            rows.append(rec)
            continue

        ok = grade(value, it.get("answer"))
        st["certified"] += 1
        st["correct" if ok else "WRONG"] += 1
        rec.update({"status": "certified", "value": value,
                    "correct": ok, "mode": trace.get("mode")})
        rows.append(rec)

    wall = time.perf_counter() - t0
    n = len(items)
    served = st["certified"]
    summ = {
        "arm": a.arm, "split": a.split, "n": n,
        "status": dict(st), "abstain_reasons": dict(abst),
        "escalation_units": dict(esc_units),
        "deterministic_coverage": round(served / n, 4) if n else None,
        "correct": st["correct"], "wrong": st["WRONG"],
        "wrong_fire": (round(st["WRONG"] / served, 5)
                       if served else None),
        "escalation_fraction": round(st["escalated"] / n, 4) if n else None,
        "ms_per_query": round(1000 * wall / n, 3) if n else None,
        "model_calls": 0,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ("%s_summary.json" % a.arm)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    with open(OUT / ("%s.jsonl" % a.arm), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
