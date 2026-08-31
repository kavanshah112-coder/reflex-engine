# -*- coding: utf-8 -*-
# origin: new for V1.3 — W2/W3/W4 runner (V1_3_SPEC §5-§7)
"""Runs the parse -> verify -> execute path over real language.

  python w2_parse.py --arm local --split traffic_unique [--limit N]
  python w2_parse.py --arm local --split full_sealed        (once)

Local arm only here; bridge arms enqueue through the batched protocol
(w2_bridge.py). Every record carries the full check report, so the
per-check attribution required by V1_3_SPEC §6 comes out of the same
run that produces coverage.
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
    ap.add_argument("--arm", default="local")
    ap.add_argument("--split", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex.frame import FrameIndex
    from reflex.parse_agent import solve
    import v10.universe10 as U10

    if a.arm == "local":
        from reflex.adapters.ollama import OllamaAdapter
        adapter = OllamaAdapter()
    else:
        raise SystemExit("bridge arms run through w2_bridge.py")

    fi = FrameIndex.load(HERE / "results/v13/frame_index.json")
    items = json.loads((DATA / f"v13_{a.split}.json")
                       .read_text(encoding="utf-8"))
    items = [x for x in items if x.get("answer") is not None]
    if a.limit:
        items = items[:a.limit]
    tag = a.tag or f"{a.arm}_{a.split}"
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{tag}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                pass

    st = Counter()
    fail_at = Counter()
    t0 = time.time()
    f = open(path, "a", encoding="utf-8")
    try:
        for i, it in enumerate(items):
            key = it.get("sid") or it["id"]
            if key in done:
                continue
            frame = fi.frame(it["q"])
            rec = solve(adapter, it["q"], frame, U10.KINDS10)
            ok = grade(rec["value"], it.get("answer"))
            st[rec["status"]] += 1
            if rec["status"] == "certified":
                st["correct" if ok else "WRONG"] += 1
            if rec["status"] == "verification_failed" and rec.get(
                    "checks"):
                first = next((k for k, v in rec["checks"].items()
                              if isinstance(v, dict)
                              and not v.get("ok")), "?")
                fail_at[first] += 1
            f.write(json.dumps({
                "id": key, "src_id": it["id"],
                "status": rec["status"], "value": rec["value"],
                "answer": it.get("answer"), "correct": ok,
                "out_of_frame": rec["out_of_frame"],
                "retried": rec.get("retried", False),
                "tokens": rec.get("tokens", 0),
                "checks": rec.get("checks"),
                "ir": rec.get("ir")}, default=str) + "\n")
            f.flush()
            if (i + 1) % 25 == 0:
                print(f"[{tag}] {i+1}/{len(items)} "
                      f"{dict(st)} ({time.time()-t0:.0f}s)",
                      flush=True)
    finally:
        f.close()
    n = sum(v for k, v in st.items()
            if k in ("certified", "verification_failed",
                     "execution_failed", "model_refused"))
    summ = {"tag": tag, "n": n, "status": dict(st),
            "first_failing_check": dict(fail_at),
            "wall_s": round(time.time() - t0)}
    (OUT / f"{tag}_summary.json").write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
