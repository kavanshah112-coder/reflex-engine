# -*- coding: utf-8 -*-
# origin: new for V1.3 — bridge parse arms (V1_3_SPEC §5)
"""Runs a parse arm through the deferred-replay bridge.

  python w2_bridge.py --model claude-haiku-4-5 --split arm_sample

Enqueues on a miss and records `pending`; service the queue with
service_bridge13.py + matching-model agents, then re-run. Iterates to
convergence. Because parses are dual and corroboration only fires for
survivors, an arm typically needs two or three servicing rounds.
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
DATA = HERE / "results" / "v13" / "data"
OUT = HERE / "results" / "v13" / "w2"
BRIDGE = HERE / "results" / "bridge_v13"


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    if a == 0:
        return abs(v) < 1e-9
    return abs(v - a) / abs(a) <= tol


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--split", default="arm_sample")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex.adapters.anthropic_bridge import \
        AnthropicBridgeAdapter
    from reflex.frame import FrameIndex
    from reflex.parse_agent import solve
    import v10.universe10 as U10

    adapter = AnthropicBridgeAdapter(
        model=a.model, bridge_dir=BRIDGE / a.model)
    fi = FrameIndex.load(HERE / "results/v13/frame_index.json")
    items = json.loads((DATA / f"v13_{a.split}.json")
                       .read_text(encoding="utf-8"))
    items = [x for x in items if x.get("answer") is not None]
    if a.limit:
        items = items[:a.limit]

    tag = f"{a.model.split('-')[1]}_{a.split}"
    OUT.mkdir(parents=True, exist_ok=True)
    st = Counter()
    fail_at = Counter()
    rows = []
    t0 = time.time()
    for it in items:
        frame = fi.frame(it["q"])
        rec = solve(adapter, it["q"], frame, U10.KINDS10)
        ok = grade(rec["value"], it.get("answer"))
        st[rec["status"]] += 1
        if rec["status"] == "certified":
            st["correct" if ok else "WRONG"] += 1
        if rec["status"] == "verification_failed" and rec.get("checks"):
            first = next((k for k, v in rec["checks"].items()
                          if isinstance(v, dict) and not v.get("ok")),
                         "?")
            fail_at[first] += 1
        rows.append({"id": it.get("sid") or it["id"],
                     "src_id": it["id"], "status": rec["status"],
                     "value": rec["value"],
                     "answer": it.get("answer"), "correct": ok,
                     "out_of_frame": rec["out_of_frame"],
                     "tokens": rec.get("tokens", 0),
                     "checks": rec.get("checks"),
                     "corroboration": rec.get("corroboration"),
                     "ir": rec.get("ir")})
    with open(OUT / f"{tag}.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    pend = len(adapter.pending())
    summ = {"tag": tag, "model": a.model, "n": len(items),
            "status": dict(st), "first_failing_check": dict(fail_at),
            "bridge_pending": pend,
            "adapter": adapter.stats(),
            "wall_s": round(time.time() - t0)}
    (OUT / f"{tag}_summary.json").write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))
    if pend:
        print(f"\nBRIDGE PENDING {pend} — run:\n"
              f"  python service_bridge13.py list {a.model}\n"
              f"  (service the batches with {a.model} agents)\n"
              f"  python service_bridge13.py ingest {a.model}\n"
              f"  python w2_bridge.py --model {a.model} "
              f"--split {a.split}")
        sys.exit(3)


if __name__ == "__main__":
    main()
